# Auto Responders

Automated message responses with trigger-based activation for common questions and server management.

## 🤖 Overview

The Sprouts auto responder system provides simple trigger-and-reply automation to help manage common questions and provide instant responses to users.

### Key Features

- **📝 Simple Trigger System** - Text-based triggers that activate on message content
- **💬 Custom Responses** - Personalized reply messages with variable support
- **⚙️ Enable/Disable Toggle** - Turn responders on/off without deletion
- **👑 Administrator Control** - Only admins can manage auto responders
- **🔄 Easy Management** - Add, edit, remove, and list responders

## 🚀 Getting Started

### View Auto Responder Commands

```
s.autoresponder
```

This shows the main auto responder help with all available subcommands and examples.

## 📝 Managing Auto Responders

### Add New Auto Responder

```
s.autoresponder add trigger:<trigger> reply:<response>
```

**Examples:**
```
s.autoresponder add trigger:hello reply:Hello there! Welcome to our server!
s.autoresponder add trigger:rules reply:Please check our #rules channel
s.autoresponder add trigger:support reply:Need help? Use s.new to create a ticket
s.autoresponder add trigger:discord reply:Join our community Discord server!
```

### Edit Existing Response

```
s.autoresponder editreply trigger:<trigger> reply:<new response>
```

**Examples:**
```
s.autoresponder editreply trigger:hello reply:Hi there! Welcome to our amazing community!
s.autoresponder editreply trigger:rules reply:📋 Server rules can be found in #rules-and-info
```

### Remove Auto Responder

```
s.autoresponder remove <trigger>
```

**Examples:**
```
s.autoresponder remove hello
s.autoresponder remove support
s.autoresponder remove rules
```

### List All Auto Responders

```
s.autoresponder list
```

Shows all auto responders configured for the server with their triggers, responses, and status.

### Toggle Auto Responder

```
s.autoresponder toggle <trigger>
```

Enable or disable an auto responder without deleting it:

**Examples:**
```
s.autoresponder toggle hello    # Disable if enabled, enable if disabled
s.autoresponder toggle support  # Toggle support responder
```

## 🎯 How Auto Responders Work

### Trigger Detection

- **Case Insensitive** - Triggers match regardless of case
- **Contains Match** - Trigger word/phrase anywhere in the message
- **First Match** - Only the first matching responder fires
- **Command Exclusion** - Won't trigger on bot commands

### Response Behavior

- **Instant Reply** - Responds immediately when triggered
- **Channel Specific** - Responds in the same channel as trigger
- **No Command Interference** - Won't interfere with bot commands
- **Single Response** - One responder per message maximum

## 💡 Best Practices

### Effective Trigger Words

**Good Triggers:**
- `hello`, `hi`, `hey` - Greetings
- `rules`, `guidelines` - Server information
- `support`, `help` - Assistance requests
- `invite`, `link` - Server promotion
- `thanks`, `thank you` - Appreciation responses

**Avoid These Triggers:**
- Single letters (`a`, `i`, `x`) - Too broad
- Common words (`the`, `and`, `is`) - Too frequent
- Command names (`ping`, `info`) - Conflicts with bot

### Response Content Ideas

**Welcome Responses:**
```
s.autoresponder add trigger:hello reply:Hello! 👋 Welcome to our server! Be sure to check out #rules and introduce yourself in #introductions!
```

**Information Responses:**
```
s.autoresponder add trigger:rules reply:📋 You can find all server rules in our #rules channel. Please read them to ensure a great experience for everyone!
```

**Support Responses:**
```
s.autoresponder add trigger:help reply:🎫 Need help? Create a support ticket with s.new and our staff will assist you!
```

**FAQ Responses:**
```
s.autoresponder add trigger:discord nitro reply:💎 Discord Nitro gives you server boosts, better audio quality, larger file uploads, and animated avatars!
```

## 🔧 Advanced Usage

### Variable Support

Auto responders support the same variables as embeds:

**Available Variables:**
- `$(user.name)` - Username of message sender
- `$(user.mention)` - Mention the user
- `$(server.name)` - Server name
- `$(server.members)` - Member count
- `$(channel)` - Current channel mention

**Example with Variables:**
```
s.autoresponder add trigger:welcome reply:Welcome $(user.mention)! You're member #$(server.members) in $(server.name)! 🎉
```

### Multi-Word Triggers

Use quotes or underscores for multi-word triggers:

**Examples:**
```
s.autoresponder add trigger:how are you reply:I'm doing great! Thanks for asking! 😊
s.autoresponder add trigger:good morning reply:Good morning! Have a wonderful day! ☀️
s.autoresponder add trigger:thank you reply:You're very welcome! Happy to help! 💙
```

## 📊 Management Tips

### Monitor Response Effectiveness

Track which auto responders are most helpful:
- **Common Questions** - Add responders for frequently asked questions
- **User Feedback** - Ask users if auto responses were helpful
- **Staff Workload** - Good responders reduce support ticket volume

### Regular Maintenance

Keep your auto responders current:
- **Update Information** - Keep server info and rules current
- **Remove Outdated** - Delete responders for old events or features
- **Test Regularly** - Make sure responses still make sense
- **Staff Training** - Ensure staff know about existing responders

### Organization Strategy

**Categorize Your Responders:**
- **Greetings** - Welcome messages and introductions
- **Information** - Rules, FAQ, server details
- **Support** - Help requests and ticket guidance
- **Community** - Events, activities, social responses

## 🔐 Permissions & Security

### Required Permissions

**For Auto Responder Management:**
- **Administrator** permission required for all auto responder commands
- Only server administrators can add, edit, remove, or toggle responders

**For Bot Functionality:**
- **Send Messages** - Bot needs to send auto responses
- **Read Messages** - Bot needs to read incoming messages
- **Embed Links** - For any embeds in responses (if applicable)

### Security Considerations

**Safe Practices:**
- ✅ Review responses before adding them
- ✅ Avoid sharing sensitive information in responses
- ✅ Keep responses professional and on-topic
- ✅ Test responses in a safe channel first

**Avoid These:**
- ❌ Personal information in responses
- ❌ External links without verification
- ❌ Controversial or sensitive topics
- ❌ Too many responders (can become spam-like)

## ❓ Troubleshooting

### Common Issues

**Auto Responder Not Triggering:**
- ✅ Check if responder is enabled: `s.autoresponder list`
- ✅ Verify trigger spelling matches message content
- ✅ Ensure bot has message read permissions
- ✅ Check if message was a command (responders don't trigger on commands)

**Response Not Sending:**
- ✅ Verify bot has send message permissions
- ✅ Check if channel allows bot messages
- ✅ Ensure response text isn't too long (2000 character limit)

**Variables Not Working:**
- ✅ Use exact variable syntax: `$(variable.name)`
- ✅ Check variable is available in context
- ✅ Test variables with simple response first

### Getting Help

Need assistance with auto responders?
- **📚 Examples** - Check the examples in this guide
- **🎫 Support** - Create a ticket with `s.new` for help
- **💬 Community** - Ask other users in support channels

---

**Next:** Learn about [Sticky Messages](sticky-messages.md) for persistent channel messages.