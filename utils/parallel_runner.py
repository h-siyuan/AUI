import asyncio
import json
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
from .progress_tracker import ProgressTracker

class ParallelRunner:
    def __init__(self, max_concurrent: int = 5, api_max_concurrent: int = None, local_max_concurrent: int = None):
        """并行任务执行器"""
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Separate concurrency for API vs local models if specified
        self.api_max_concurrent = api_max_concurrent or max_concurrent
        self.local_max_concurrent = local_max_concurrent or max_concurrent
        self.api_semaphore = asyncio.Semaphore(self.api_max_concurrent) if api_max_concurrent else None
        self.local_semaphore = asyncio.Semaphore(self.local_max_concurrent) if local_max_concurrent else None
        
    async def run_parallel_tasks(self, 
                                models: List[str], 
                                apps: List[str],
                                task_func: Callable,
                                stage_name: str,
                                valid_combinations: Optional[List[tuple]] = None,
                                **kwargs) -> Dict[str, Any]:
        """并行运行模型×应用的任务矩阵"""
        
        # 创建进度跟踪器
        progress_tracker = ProgressTracker(stage_name, models, apps)
        
        # 创建所有任务
        tasks = []
        for model_name in models:
            for app_name in apps:
                # 如果指定了valid_combinations，只处理有效的组合
                if valid_combinations is not None:
                    if (model_name, app_name) not in valid_combinations:
                        continue
                
                task = asyncio.create_task(
                    self._run_single_task(
                        task_func, model_name, app_name, 
                        progress_tracker, **kwargs
                    )
                )
                tasks.append((model_name, app_name, task))
        
        # 启动进度显示
        progress_task = asyncio.create_task(progress_tracker.display_loop())
        
        # 等待所有任务完成
        results = []
        for model_name, app_name, task in tasks:
            result = await task
            results.append({
                'model': model_name,
                'app': app_name,
                'result': result
            })
        
        # 停止进度显示
        progress_tracker.stop()
        await progress_task
        
        # 收集错误信息
        all_errors = progress_tracker.get_all_errors()
        successful_count = len([r for r in results if r['result'].get('success')])
        failed_count = len(results) - successful_count
        
        summary = {
            'stage': stage_name,
            'total_tasks': len(results),
            'successful_tasks': successful_count,
            'failed_tasks': failed_count,
            'results': results,
            'errors': all_errors
        }
        
        ts_print(f"\n{stage_name} Complete: {successful_count} success, {failed_count} failed")
        
        return summary
    
    def _get_model_semaphore(self, model_name: str):
        """统一使用默认信号量，避免隐式回退与隐藏配置问题"""
        return self.semaphore
    
    async def _run_single_task(self, 
                              task_func: Callable, 
                              model_name: str, 
                              app_name: str,
                              progress_tracker: ProgressTracker,
                              **kwargs) -> Dict[str, Any]:
        """运行单个任务"""
        semaphore = self._get_model_semaphore(model_name)
        
        async with semaphore:
            progress_tracker.update_status(model_name, app_name, "🚀 Starting...")
            
            try:
                # 执行实际任务
                if asyncio.iscoroutinefunction(task_func):
                    result = await task_func(model_name, app_name, progress_tracker, **kwargs)
                else:
                    result = task_func(model_name, app_name, progress_tracker, **kwargs)
                
                # 根据任务结果更新状态
                if result.get('success'):
                    progress_tracker.update_status(model_name, app_name, "✅ Done")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    short_error = f"❌ Failed: {error_msg}"
                    progress_tracker.update_status(
                        model_name, app_name, short_error,
                        error_detail=error_msg
                    )
                
                return result
                
            except Exception as e:
                # 获取完整错误信息
                import traceback
                full_error = traceback.format_exc()
                error_summary = str(e)
                
                # 网格显示完整错误信息
                short_error = f"❌ Failed: {error_summary}"
                progress_tracker.update_status(
                    model_name, app_name, short_error, 
                    error_detail=f"{error_summary}\n\nFull traceback:\n{full_error}"
                )
                
                # 返回错误结果而不是抛出异常，保持程序继续运行
                return {
                    'error': error_summary,
                    'full_error': full_error,
                    'model': model_name,
                    'app': app_name,
                    'success': False
                }
    
    def save_incremental_progress(self, 
                                 stage_name: str,
                                 model_name: str, 
                                 app_name: str, 
                                 data: Dict[str, Any],
                                 base_dir: Optional[str] = None):
        """保存增量进度"""
        if base_dir:
            progress_dir = Path(base_dir) / "progress" / stage_name
        else:
            # Anchor to repo progress directory by default
            progress_dir = Path(__file__).resolve().parents[1] / "progress" / stage_name
        
        progress_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存任务级别的进度
        task_file = progress_dir / f"{model_name}_{app_name}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 更新阶段级别的汇总
        summary_file = progress_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        else:
            summary = {'completed_tasks': []}
        
        task_id = f"{model_name}_{app_name}"
        # 移除旧记录
        summary['completed_tasks'] = [t for t in summary['completed_tasks'] if t != task_id]
        
        # 添加新记录（包括错误信息）
        if data.get('error'):
            summary['completed_tasks'].append({
                'task_id': task_id,
                'status': 'failed',
                'error': data.get('error'),
                'full_error': data.get('full_error')
            })
        else:
            summary['completed_tasks'].append({
                'task_id': task_id,
                'status': 'success'
            })
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
from .logging_utils import ts_print
