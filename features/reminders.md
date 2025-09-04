# Reminders

Personal reminder system with flexible time parsing for scheduling notifications.

## ⏰ Overview

The Sprouts reminder system helps you schedule personal notifications with natural language time parsing, perfect for keeping track of tasks, events, and important deadlines.

### Key Features

- **🕒 Flexible Time Parsing** - Natural language and precise time formats
- **📱 Personal Notifications** - Reminders sent via DM and channel mention
- **📋 Reminder Management** - View, edit, and delete active reminders
- **⏳ Multiple Time Formats** - Relative times, exact times, and complex combinations
- **💾 Persistent Storage** - Reminders survive bot restarts

## 🚀 Setting Reminders

### Basic Reminder Syntax

```
s.remind <time> <message>
```

The reminder system accepts various time formats and will notify you when the time expires.

### Time Format Examples

**Relative Times:**
```
s.remind 30m Take a break
s.remind 2h Team meeting
s.remind 1d Submit report
s.remind 1w Doctor appointment
```

**Complex Times:**
```
s.remind 1d2h3m Server maintenance tomorrow
s.remind 45s Quick reminder to check the oven
s.remind 3w2d1h Event planning deadline
```

**Exact Times (if supported):**
```
s.remind tomorrow at 3pm Team standup
s.remind next friday at 2:30pm Weekly review
```

## ⏱️ Time Format Reference

### Supported Time Units

| Unit | Abbreviation | Example |
|------|-------------|---------|
| Seconds | `s`, `sec`, `seconds` | `30s`, `45sec` |
| Minutes | `m`, `min`, `minutes` | `15m`, `30min` |
| Hours | `h`, `hr`, `hours` | `2h`, `3hr` |
| Days | `d`, `day`, `days` | `1d`, `2days` |
| Weeks | `w`, `week`, `weeks` | `1w`, `2weeks` |

### Combination Examples

**Multiple Units:**
```
s.remind 1h30m Lunch break
s.remind 2d12h Weekend trip
s.remind 1w3d2h Project deadline
```

**Natural Language:**
```
s.remind in 5 minutes Check the laundry
s.remind tomorrow morning Morning workout
s.remind next week Team retrospective
```

## 📋 Managing Reminders

### View Your Reminders

```
s.reminders
```

Shows all your active reminders with:
- **Reminder ID** - Unique identifier for management
- **Message** - The reminder text
- **Time Remaining** - How long until notification
- **Created** - When you set the reminder

### Delete Specific Reminder

```
s.delreminder <reminder_id>
```

Remove a reminder using its ID from the reminders list.

**Examples:**
```
s.delreminder 1    # Delete reminder with ID 1
s.delreminder 5    # Delete reminder with ID 5
```

### Reminder Aliases

The reminder commands have alternative names:
```
s.remind = s.remindme = s.setr
s.reminders = s.myreminders  
s.delreminder = s.removereminder
```

## 💡 Practical Examples

### Daily Tasks

**Work Reminders:**
```
s.remind 9h Start of workday - check emails
s.remind 13h Lunch break time
s.remind 17h End of workday - save work
s.remind 1d Daily standup meeting
```

**Personal Reminders:**
```
s.remind 30m Water the plants
s.remind 2h Take medication
s.remind 4h Call mom
s.remind 1d Pay rent
```

### Event Planning

**Meeting Preparation:**
```
s.remind 1d Meeting tomorrow - prepare slides
s.remind 2h Meeting in 2 hours - join Zoom
s.remind 15m Meeting starting soon
```

**Project Deadlines:**
```
s.remind 1w Project deadline next week
s.remind 3d Final review in 3 days
s.remind 1d Submit project tomorrow
```

### Health & Wellness

**Exercise Reminders:**
```
s.remind 1h Gym workout time
s.remind 2d Rest day - no heavy lifting
s.remind 1w Weigh-in day
```

**Medication & Health:**
```
s.remind 8h Morning medication
s.remind 12h Afternoon pills
s.remind 1d Doctor appointment tomorrow
```

## 🎯 Best Practices

### Effective Reminder Messages

**Be Specific:**
```
✅ s.remind 1h Team meeting in Conference Room A
❌ s.remind 1h meeting
```

**Include Context:**
```
✅ s.remind 2d Submit quarterly report to Sarah by 5 PM
❌ s.remind 2d report
```

**Add Action Items:**
```
✅ s.remind 30m Call client about contract renewal - have proposal ready
❌ s.remind 30m call client
```

### Time Management Tips

**Buffer Time:**
```
s.remind 1h15m Meeting in 75 minutes - start preparing now
s.remind 45m Leave for appointment in 45 minutes
```

**Multiple Reminders:**
```
s.remind 1w Project due next week - start planning
s.remind 3d Project due in 3 days - begin implementation  
s.remind 1d Project due tomorrow - final review
s.remind 2h Project deadline in 2 hours - submit now
```

### Organization Strategies

**Categorize by Time:**
- **Short-term** (< 1 hour): Immediate tasks, breaks
- **Medium-term** (1 hour - 1 day): Meetings, appointments
- **Long-term** (> 1 day): Deadlines, events

**Categorize by Type:**
- **Work**: Meetings, deadlines, tasks
- **Personal**: Health, family, hobbies
- **Events**: Appointments, celebrations, travel

## ⚙️ Advanced Usage

### Complex Time Combinations

**Multi-stage Reminders:**
```
s.remind 1w Big presentation next week - start outline
s.remind 5d Presentation Friday - create slides
s.remind 2d Presentation Wednesday - practice run
s.remind 2h Presentation in 2 hours - final prep
```

**Recurring Task Planning:**
```
s.remind 1d Weekly team sync tomorrow
s.remind 1w Next weekly team sync  
s.remind 2w Team sync in 2 weeks
```

### Event Coordination

**Conference/Event Planning:**
```
s.remind 1w Conference registration closes next week
s.remind 3d Conference travel arrangements - book hotel
s.remind 1d Conference tomorrow - pack materials
s.remind 2h Conference keynote in 2 hours
```

## 🔔 Notification Behavior

### How Reminders Notify You

**Delivery Methods:**
1. **Direct Message** - Private notification from the bot
2. **Channel Mention** - Tagged in the original channel (if accessible)
3. **Fallback Channel** - Server's default channel if original unavailable

**Notification Content:**
- **Original Message** - Your reminder text
- **Timestamp** - When you set the reminder
- **Context** - Which server/channel it was set in

### Privacy & Security

**Personal Reminders:**
- ✅ Only you receive reminder notifications
- ✅ Reminders are stored securely
- ✅ Other users cannot see your reminders
- ✅ DM notifications keep reminders private

## 📊 Reminder Limits

### System Limitations

**Per User Limits:**
- **Maximum Active Reminders**: Typically 10-20 per user
- **Maximum Time**: Usually up to 1 year in advance
- **Minimum Time**: At least 1 second

**Time Accuracy:**
- **Precision**: Within 1-2 seconds of target time
- **Reliability**: Survives bot restarts and updates
- **Time Zones**: Uses server time (typically UTC)

### Performance Considerations

**Optimal Usage:**
- Keep active reminder count reasonable (< 10)
- Delete completed or unnecessary reminders
- Use appropriate time intervals (not too short)

## ❓ Troubleshooting

### Common Issues

**Reminder Not Working:**
- ✅ Check time format: `s.remind 30m test message`
- ✅ Verify you can receive DMs from the bot
- ✅ Ensure reminder message isn't empty
- ✅ Check your active reminders: `s.reminders`

**Time Parsing Errors:**
- ✅ Use simple formats: `1h30m`, `2d`, `45m`
- ✅ Avoid ambiguous times like "tomorrow" without specific time
- ✅ Check for typos in time units: `30min` not `30mins`

**Notification Not Received:**
- ✅ Check DM settings allow messages from server members
- ✅ Verify bot has permission to DM you
- ✅ Check if you left the server where reminder was set
- ✅ Look for notification in original channel

**Cannot Delete Reminder:**
- ✅ Use exact reminder ID from `s.reminders` list
- ✅ Check if reminder already expired automatically
- ✅ Verify reminder belongs to you

### Time Zone Considerations

**Server Time:**
- Bot typically uses UTC time
- Check bot timezone if reminders seem off
- Consider your local timezone when setting times

**Best Practices:**
- Set reminders relative to current time
- Use specific durations rather than exact times
- Test with short reminders first

## 🎮 Fun & Creative Uses

### Gaming Reminders

**Game Events:**
```
s.remind 1h Raid starts in 1 hour - log in early
s.remind 30m Daily quests reset in 30 minutes
s.remind 2d Weekend tournament signup closes
```

### Social Activities

**Community Events:**
```
s.remind 1h Movie night starts in 1 hour
s.remind 30m Game night beginning soon
s.remind 1d Community meetup tomorrow
```

### Learning & Development

**Study Schedule:**
```
s.remind 1h Study session - Chapter 5 review
s.remind 2d Quiz on Wednesday - review notes
s.remind 1w Final exam next week - start cramming
```

---

**Next:** Learn about [Utilities](utilities.md) for server information and management tools.