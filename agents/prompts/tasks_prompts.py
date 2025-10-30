"""
Task generation prompts for Stage 0 (extracted verbatim). Do not modify content.
"""

def build_base_prompt(tag_type: str, app_title: str, app_description: str,
                      tag_specific_content: str, primary_tag: str) -> str:
    return """Generate 30 diverse, realistic user tasks for the following {tag_type} application:

Application: {app_title}
Description: {app_description}

IMPORTANT CONSTRAINTS:
- External system interactions such as file uploads and downloads are not available

Each task should be:
- Clear and specific in its description
- Represent realistic user scenarios
- Cover different complexity levels and use cases
- Include proper expected outcomes for verification
- Avoid single element grounding (focus on complete workflows)
- Test the application's core functionality effectively

{tag_specific_content}

Generate exactly 30 tasks with tag-specific focus on {primary_tag} testing philosophy.""".format(
        tag_type=tag_type,
        app_title=app_title,
        app_description=app_description,
        tag_specific_content=tag_specific_content,
        primary_tag=primary_tag,
    )


def get_tag_based_prompt_template(tags: list) -> str:
    if not tags:
        tags = ['app']
    primary_tag = tags[0].lower()

    if primary_tag == 'game':
        return """Focus on GAME-SPECIFIC user tasks:
1. Playing complete game rounds or levels
2. Achieving high scores and personal bests
3. Completing specific game objectives or challenges
4. Using game controls and input methods
5. Navigating game menus and settings
6. Restarting games and trying different strategies
7. Progressing through difficulty levels

Additional task requirements:
- Focus on actual gameplay actions and goals
- Include winning and losing scenarios
- Cover different skill levels and strategies
- Test game restart and replay functionality
- Emphasize user enjoyment and engagement"""

    elif primary_tag == 'tool':
        return """Focus on TOOL-SPECIFIC user tasks:
1. Creating or generating content using the tool
2. Inputting data in various formats and types (typed/pasted text or on-page controls)
3. Transforming and processing information
4. Previewing results in-page (no file uploads/downloads)
5. Using tool-specific features and options
6. Working with both simple and complex inputs
7. Completing end-to-end workflows within the page

Additional task requirements:
- Focus on practical use cases and workflows
- Include both basic and advanced tool usage
- Cover different input types and scenarios without external files
- Verify visible in-page outputs or status changes in the DOM
- Emphasize real-world problem solving"""

    elif primary_tag == 'utility':
        return """Focus on UTILITY-SPECIFIC user tasks:
1. Setting up and configuring the utility for personal use
2. Adding, organizing, and managing data or items
3. Tracking progress and monitoring status over time
4. Using timers, reminders, and scheduling features
5. Customizing settings and preferences
6. Completing daily or routine activities
7. Accessing and updating information quickly

Additional task requirements:
- Focus on everyday productivity scenarios
- Include setup and personalization tasks
- Cover routine and habitual usage patterns
- Test organization and tracking features
- Emphasize practical daily life applications"""

    elif primary_tag == 'interactive':
        return """Focus on INTERACTIVE-SPECIFIC user tasks:
1. Exploring and experimenting with interactive elements
2. Creating and manipulating visual or audio content
3. Adjusting parameters and settings in real-time
4. Playing with creative tools and features
5. Experiencing immersive visual or audio effects
6. Using touch, click, and gesture interactions
7. Customizing appearance and behavior

Additional task requirements:
- Focus on creative and exploratory activities
- Include experimentation and play scenarios
- Cover different interaction methods
- Test customization and personalization
- Emphasize sensory and aesthetic experiences"""

    elif primary_tag == 'landing':
        return """Focus on LANDING-SPECIFIC user tasks:
1. Browsing and exploring page content and sections
2. Reading and understanding key information
3. Clicking on call-to-action buttons and links
4. Navigating through different page sections
5. Finding contact information and ways to engage
6. Viewing team, product, or service details
7. Accessing additional resources and links

Additional task requirements:
- Focus on visitor browsing and exploration
- Include information-seeking behaviors
- Cover engagement and conversion actions
- Test navigation and content discovery
- Emphasize typical visitor journey scenarios"""

    else:
        return """Focus on APP-SPECIFIC user tasks:
1. Creating, editing, and managing content or data
2. Using multiple features in combination
3. Setting up and personalizing the application
4. Completing complex multi-step workflows
5. Organizing and categorizing information
6. Accessing and updating saved information

Additional task requirements:
- Focus on practical in-app usage
- Include multi-feature workflows and combinations
- Cover content creation and management
- Test personalization and customization
- Verify completion via visible state changes in the DOM (no external integrations)"""

