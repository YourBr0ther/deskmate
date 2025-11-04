# DeskMate User Guide

Welcome to DeskMate, your virtual AI companion! This guide will help you get started and make the most of your experience with your AI companion.

## Table of Contents

1. [What is DeskMate?](#what-is-deskmate)
2. [Getting Started](#getting-started)
3. [Interface Overview](#interface-overview)
4. [Interacting with Your Companion](#interacting-with-your-companion)
5. [Room Environment](#room-environment)
6. [Settings and Customization](#settings-and-customization)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Tips and Best Practices](#tips-and-best-practices)

## What is DeskMate?

DeskMate is a virtual AI companion that lives in a simulated room environment on your computer. Your companion can:

- **Chat with you** in natural conversation
- **Move around** their virtual room
- **Interact with objects** like lamps, furniture, and decorations
- **Remember** your conversations and preferences
- **Express emotions** through mood changes and expressions
- **Help with tasks** and provide companionship

DeskMate is designed to run on a secondary monitor in kiosk mode (1920x480 resolution) for the optimal experience, but it also works great in a browser window.

## Getting Started

### First Launch

1. **Open DeskMate** in your web browser at `http://localhost:3000`
2. **Wait for loading** - You'll see the room environment and your companion appear
3. **Check connection** - Look for a green dot indicating the system is connected
4. **Say hello!** - Type a message in the chat box to start your first conversation

### Your First Conversation

Try these starter messages:
- "Hello! What's your name?"
- "Can you show me around the room?"
- "What can you do?"
- "How are you feeling today?"

Your companion will respond and may move around or interact with objects in their room.

## Interface Overview

### Desktop Layout (1920x480)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Room View (1280x480)              │  Companion Panel (640x480)          │
│  ┌──────────────────────────────┐  │  ┌────────────────────────────────┐ │
│  │                              │  │  │  [Portrait 400x400]            │ │
│  │   Virtual Room               │  │  │                                │ │
│  │   (64x16 grid)               │  │  │  Character Name                │ │
│  │                              │  │  │  ────────────────              │ │
│  │   🧑‍💼 Assistant                 │  │  │  Status: Active             │ │
│  │   🏠 Furniture & Objects       │  │  │  Mood: Happy                │ │
│  │                              │  │  │  Activity: Chatting           │ │
│  └──────────────────────────────┘  │  └────────────────────────────────┘ │
│                                     │                                    │
│                                     │  [Chat Window - 640x80]            │
│                                     │  [Input Box]                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout

On mobile devices, the interface adapts to a stacked layout:
- Room view on top
- Companion panel and chat below
- Touch-friendly controls

### Key Interface Elements

#### 1. Room View (Left Side)
- **Grid Environment**: 64x16 cell room where your companion lives
- **Assistant Indicator**: White dot showing your companion's location
- **Objects**: Furniture and items your companion can interact with
- **Interactive Areas**: Click to direct your companion's movement

#### 2. Companion Panel (Right Side)
- **Portrait**: Visual representation of your companion
- **Status Information**: Current activity, mood, and energy level
- **Time Display**: Current time and date with smart formatting
- **Performance Monitor**: Optional FPS and system metrics

#### 3. Chat Interface
- **Message History**: Scrollable conversation log
- **Input Box**: Type your messages here
- **Send Button**: Submit messages (or press Enter)
- **Settings Button**: Access configuration options

#### 4. Status Indicators
- **Connection**: 🟢 Connected / 🔴 Disconnected
- **Model Info**: Current AI model (Ollama/Nano-GPT)
- **Typing Indicator**: Shows when your companion is thinking
- **Activity Status**: What your companion is currently doing

## Interacting with Your Companion

### Chat Commands

#### Basic Conversation
```
"Hello, how are you?"
"What's your favorite object in the room?"
"Tell me about yourself"
"How are you feeling today?"
```

#### Movement Commands
```
"Move to the desk"
"Go to position 20, 10"
"Walk over to the window"
"Come closer to me"
```

#### Object Interaction
```
"Turn on the lamp"
"Sit on the bed"
"Open the window"
"Look at the bookshelf"
```

#### Room Exploration
```
"What can you see from there?"
"Describe the room"
"What objects are nearby?"
"Show me around"
```

#### Emotional Interaction
```
"I'm feeling happy today"
"You're doing great!"
"I need some comfort"
"Can you cheer me up?"
```

### Direct Room Interaction

#### Grid Clicks
- **Left-click empty space**: Your companion will move there
- **Left-click objects**: Select/interact with objects
- **Right-click objects**: Context-specific interactions (sit, activate, etc.)

#### Drag and Drop
- **Movable objects** can be dragged to new positions
- **Visual feedback** shows valid drop zones
- **Collision detection** prevents invalid placements

### Advanced Interactions

#### Multi-step Requests
```
"Turn on the lamp, then move to the bed and sit down"
"I want to relax - suggest some activities and help me with them"
"Clean up the room by organizing the objects"
```

#### Context-aware Requests
```
"Remember that I like bright lighting"
"Based on our previous conversations, what should we do now?"
"I'm tired - what do you recommend?"
```

## Room Environment

### Objects in the Room

#### Large Furniture (Immovable)
- **Bed**: Comfortable sleeping area - your companion can sit here
- **Desk**: Work surface with lamp and decorations
- **Window**: Provides light and can be opened/closed
- **Door**: Room entrance (decorative)
- **Bookshelf**: Storage for books and decorative items

#### Interactive Items (Movable)
- **Lamp**: Can be turned on/off, provides room lighting
- **Books**: Can be picked up, moved, and "read"
- **Decorative Objects**: Plants, frames, and personal items
- **Storage Items**: Containers and organizational objects

### Object States
Objects have various states that affect interactions:
- **Power States**: on/off for electronic items
- **Position States**: open/closed for doors and windows
- **Condition States**: clean/dirty, organized/messy
- **Interaction States**: available/in-use

### Room Physics
- **Pathfinding**: Your companion automatically navigates around obstacles
- **Collision Detection**: Objects can't overlap or be placed in invalid positions
- **Spatial Relationships**: Distance affects interaction possibilities
- **Visibility**: Your companion can only interact with nearby objects

## Settings and Customization

### Accessing Settings
- Click the **gear icon** (⚙️) in the top-right corner
- Use keyboard shortcut: `Ctrl + ,` (Windows/Linux) or `Cmd + ,` (Mac)

### Settings Categories

#### Display Settings
- **Theme**: Dark, Light, or Auto (follows system)
- **Grid Display**: Full, Minimal, or Hidden grid lines
- **Animations**: Enable/disable smooth movement animations
- **Performance**: FPS counter and performance metrics
- **Panel Transparency**: Adjust UI element transparency

#### AI Models
- **Default Provider**: Choose between Ollama (local) or Nano-GPT (cloud)
- **Model Selection**: Pick specific AI models for different capabilities
- **Auto-Select**: Let the system choose the best model for each task
- **Parameters**: Adjust temperature, max tokens, and other AI settings

#### Chat Settings
- **Timestamps**: Show/hide message timestamps
- **Typing Indicator**: Enable companion "thinking" animations
- **Message History**: Set how many messages to retain
- **Auto-scroll**: Automatically scroll to new messages
- **Font Size**: Adjust chat text size

#### Notifications
- **Sound Effects**: Enable/disable audio feedback
- **Desktop Notifications**: System notifications for important events
- **Error Alerts**: How to handle connection or system errors

#### Debug Options
- **Debug Mode**: Show technical information and logs
- **Performance Monitor**: Detailed system performance metrics
- **Log Level**: Control verbosity of system logging
- **Developer Tools**: Access advanced debugging features

### Persona Management

#### Loading Custom Personas
1. Go to Settings → Personas
2. Click "Load Persona"
3. Select a SillyTavern V2 compatible PNG file
4. Your companion will adopt the new personality

#### Creating Personas
DeskMate supports SillyTavern V2 persona cards:
- Use existing persona creation tools
- Export as PNG with embedded JSON metadata
- Include character description, personality, and example dialogues

## Advanced Features

### Brain Council System

DeskMate uses an advanced "Brain Council" AI reasoning system:

#### Council Members
1. **Personality Core**: Maintains character consistency
2. **Memory Keeper**: Manages conversation history and context
3. **Spatial Reasoner**: Understands room layout and object relationships
4. **Action Planner**: Suggests appropriate actions and activities
5. **Validator**: Ensures actions are safe and make sense

#### What This Means for You
- **Consistent Character**: Your companion maintains their personality across conversations
- **Contextual Memory**: They remember previous interactions and preferences
- **Smart Actions**: Movement and object interactions are planned intelligently
- **Natural Responses**: Multiple perspectives create more human-like conversations

### Memory System

#### Types of Memory
- **Conversation Memory**: What you've talked about
- **Action Memory**: What your companion has done
- **Preference Memory**: Your likes, dislikes, and habits
- **Context Memory**: Situational awareness and room state

#### Memory Management
```
Clear Current Chat: Removes current conversation
Clear All Memory: Completely resets your companion (destructive!)
Clear Persona Memory: Removes memories for a specific character
```

### Idle Mode

When you're away, your companion enters Idle Mode:
- **Autonomous Behavior**: They act independently with lightweight AI
- **Dream Storage**: Idle activities are stored as "dreams"
- **Energy Conservation**: Reduced processing for efficiency
- **Wake on Return**: Full functionality resumes when you return

### Performance Monitoring

Track system performance:
- **FPS Counter**: Monitor rendering performance
- **Memory Usage**: RAM consumption tracking
- **Response Times**: AI processing speed
- **WebSocket Status**: Connection quality monitoring

## Troubleshooting

### Common Issues

#### Connection Problems
**Symptoms**: Red connection indicator, no responses
**Solutions**:
1. Check that backend service is running (port 8000)
2. Refresh the browser page
3. Check network connectivity
4. Restart DeskMate services

#### Slow Responses
**Symptoms**: Long delays in AI responses
**Solutions**:
1. Switch to a faster AI model in settings
2. Clear conversation memory to reduce context
3. Check system resources (CPU/RAM usage)
4. Restart services if memory usage is high

#### Assistant Not Moving
**Symptoms**: Movement commands don't work
**Solutions**:
1. Check that pathfinding is working (try different positions)
2. Ensure target position isn't blocked by objects
3. Verify WebSocket connection is active
4. Try using chat commands instead of direct clicks

#### Missing Objects or Interface Elements
**Symptoms**: Room appears empty or incomplete
**Solutions**:
1. Wait for full loading (initial load can take 30 seconds)
2. Check browser console for errors
3. Try refreshing the page
4. Verify backend database connectivity

### Performance Issues

#### High CPU Usage
- Switch to lighter AI models
- Disable performance monitoring
- Reduce animation quality
- Clear browser cache

#### Memory Leaks
- Restart browser regularly during long sessions
- Clear conversation memory periodically
- Close other browser tabs
- Monitor system memory usage

#### Rendering Problems
- Update browser to latest version
- Disable hardware acceleration if issues persist
- Try different browser (Chrome, Firefox, Safari)
- Check graphics driver updates

### Getting Help

#### Debug Information
1. Enable Debug Mode in settings
2. Open browser developer console (F12)
3. Check for error messages
4. Copy relevant logs for support

#### Support Channels
- Check the troubleshooting documentation
- Review system requirements
- Submit bug reports with debug logs
- Community forums and discussions

## Tips and Best Practices

### For the Best Experience

#### Conversation Tips
- **Be specific**: "Turn on the desk lamp" vs "turn on light"
- **Use context**: Reference previous conversations and actions
- **Be patient**: Complex requests may take time to process
- **Experiment**: Try different ways of asking for the same thing

#### Performance Tips
- **Regular maintenance**: Clear memory occasionally for better performance
- **Optimal setup**: Use recommended browser and system specifications
- **Monitor resources**: Keep an eye on CPU and memory usage
- **Network stability**: Ensure stable internet for cloud AI models

#### Customization Tips
- **Persona selection**: Choose characters that match your interaction style
- **Model optimization**: Experiment with different AI models for various tasks
- **Setting adjustment**: Fine-tune settings for your hardware capabilities
- **Memory management**: Balance memory retention with performance

### Advanced Usage

#### Power User Features
- **Keyboard shortcuts**: Learn shortcuts for faster interaction
- **Batch commands**: Combine multiple actions in single requests
- **Context building**: Reference previous conversations for deeper interaction
- **Performance monitoring**: Use debug tools to optimize your setup

#### Creative Applications
- **Storytelling**: Create narratives with your companion
- **Role-playing**: Use different personas for various scenarios
- **Problem-solving**: Discuss ideas and get different perspectives
- **Relaxation**: Use as a calming presence during work or study

### Privacy and Data

#### Local First
- All conversations stored locally on your machine
- No data sent to external servers except for cloud AI models
- Full control over your data and privacy

#### Data Management
- Regular backups recommended for important conversations
- Memory clearing is permanent - backup first if needed
- Persona files are stored locally and can be backed up

---

## Getting Started Checklist

- [ ] Launch DeskMate and verify connection (green indicator)
- [ ] Send your first message and wait for response
- [ ] Try moving your companion around the room
- [ ] Experiment with object interactions
- [ ] Explore the settings panel
- [ ] Set up your preferred AI model and persona
- [ ] Customize display and chat settings
- [ ] Try some of the example commands from this guide
- [ ] Check out the advanced features when ready

Welcome to your new AI companion experience! Take your time exploring and don't hesitate to experiment with different features and interactions.

---

*For technical documentation and developer resources, see the [Developer Guide](DEVELOPER_GUIDE.md).*