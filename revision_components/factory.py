"""
Revision Component Factory

Provides easy access to different revision components with proper initialization.
"""

from typing import Optional
from .cua_failure import CuaFailureRevision
from .unsupported import UnsupportedTasksRevision
from .integrated import IntegratedRevision

class RevisionComponentFactory:
    """Factory for creating revision components"""
    
    @staticmethod
    def create_component(component_type: str, coder, commenter=None, max_concurrent=10,
                         revision_variant: str = None, commenter_variant: str = None):
        """Create a revision component
        
        Args:
            component_type: Type of component ('cua_failure', 'unsupported', 'integrated')
            coder: Coder agent instance
            commenter: Commenter agent instance (required for MCTS)
            max_concurrent: Maximum concurrent commenter calls
            
        Returns:
            RevisionComponent instance
        """
        if component_type == 'cua_failure':
            return CuaFailureRevision(
                coder, commenter, max_concurrent=max_concurrent,
                revision_variant=(revision_variant or 'cua'),
                commenter_variant=commenter_variant
            )
        elif component_type == 'unsupported':
            return UnsupportedTasksRevision(coder, commenter, max_concurrent=max_concurrent)
        elif component_type == 'integrated':
            return IntegratedRevision(
                coder, commenter, max_concurrent=max_concurrent,
                revision_variant=(revision_variant or 'integrated'),
                commenter_variant=commenter_variant
            )
        else:
            raise ValueError(f"Unknown component type: {component_type}. "
                           f"Valid types: 'cua_failure', 'unsupported', 'integrated'")
    
    @staticmethod
    def get_available_components():
        """Get list of available component types"""
        return ['cua_failure', 'unsupported', 'integrated']
