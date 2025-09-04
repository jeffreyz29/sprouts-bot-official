# Logging System

Comprehensive logging and monitoring system for tracking bot activity, user interactions, and server events.

## 📋 Overview

The Sprouts logging system provides detailed tracking and monitoring capabilities to help server administrators understand bot usage, monitor user behavior, and maintain server security.

### Key Features

- **💬 Command Logging** - Track all bot command usage
- **📨 DM Logging** - Monitor direct messages to the bot
- **📊 Event Logging** - Server events and member activities
- **🔍 Detailed Analytics** - User behavior and usage patterns
- **⚡ Real-time Monitoring** - Instant notifications and logs

## 💬 Command Logging

### Enable Command Logging

Set up command logging to track bot usage:

```
# Available through developer commands (bot owner only)
s.cmdlogs set #bot-commands
```

### What Gets Logged

**Command Information:**
- **User Details** - Who used the command
- **Command Used** - Exact command and arguments
- **Channel Context** - Where the command was used
- **Timestamp** - When the command was executed
- **Server Info** - Which server (for multi-server bots)

**Example Log Entry:**
```
[2024-03-15 14:30:25] Command Used
User: @JohnDoe (ID: 123456789)
Command: s.userinfo @Alice
Channel: #general (ID: 987654321)
Server: My Server (ID: 555666777)
```

### Command Logging Benefits

**Server Administration:**
- Track command usage patterns
- Identify heavy bot users
- Monitor command abuse or spam
- Analyze popular features

**Security Monitoring:**
- Detect unusual command patterns
- Monitor administrative command usage
- Track potential bot abuse
- Identify automation or bot users

## 📨 DM Logging

### Enable DM Logging

Monitor direct messages sent to the bot:

```
# Available through developer commands (bot owner only)  
s.dmlogs set #dm-logs
```

### What Gets Logged

**DM Information:**
- **User Details** - Who sent the message
- **Message Content** - Full message text (when appropriate)
- **Timestamp** - When message was sent
- **Attachment Info** - Files or media sent
- **Context** - Any related server interactions

**Example Log Entry:**
```
[2024-03-15 15:45:12] DM Received
User: @Alice (ID: 987654321)  
Content: "Hi! I need help with the ticket system"
Attachments: None
Context: Member of "My Server"
```

### DM Logging Use Cases

**Support Management:**
- Track support requests via DM
- Monitor user feedback and suggestions
- Identify common questions or issues
- Provide context for support staff

**Security Monitoring:**
- Detect spam or abuse attempts
- Monitor for inappropriate content
- Track potential security threats
- Identify coordinated harassment

## 📊 Event Logging

### Enable Guild Event Logging

Track server events and member activities:

```
# Available through developer commands (bot owner only)
s.guildlogs set #event-logs
```

### What Gets Logged

**Member Events:**
- Member joins and leaves
- Role additions and removals  
- Nickname changes
- Member timeouts and bans

**Server Events:**
- Channel creation, deletion, modification
- Role creation, deletion, permission changes
- Server settings modifications
- Bot permissions changes

**Example Log Entries:**
```
[2024-03-15 16:20:33] Member Joined
User: @NewUser (ID: 111222333)
Account Created: 2024-03-10
Server: My Server (ID: 555666777)

[2024-03-15 16:25:15] Role Added
User: @Member (ID: 444555666)
Role: @Verified (ID: 777888999)
Added By: @Moderator (ID: 123789456)
Server: My Server (ID: 555666777)
```

## 🔍 Log Analysis and Insights

### Usage Patterns

**Command Usage Analytics:**
- Most popular commands
- Peak usage hours
- User engagement levels
- Feature adoption rates

**User Behavior Tracking:**
- Active vs passive users
- Command frequency per user
- Support request patterns
- Community engagement metrics

### Security Insights

**Anomaly Detection:**
- Unusual command patterns
- Sudden spikes in DM messages
- Rapid-fire command usage
- Off-hours activity spikes

**Threat Identification:**
- Coordinated spam attempts
- Bot account detection
- Permission escalation attempts
- Social engineering attempts

## ⚙️ Log Configuration

### Dual Confirmation System

When setting up logging channels, the bot provides dual confirmations:

1. **Command Channel** - Immediate confirmation where command was used
2. **Logging Channel** - Test message sent to the configured log channel

**Example Process:**
```
# Administrator runs:
s.cmdlogs set #bot-commands

# Bot responds in current channel:
"✅ Command logging enabled for #bot-commands"

# Bot also sends to #bot-commands:
"🔧 This channel is now receiving command logs"
```

### Log Channel Requirements

**Channel Permissions:**
- Bot needs **Send Messages** permission
- Bot needs **Embed Links** permission for formatted logs
- Bot needs **Read Message History** for context
- Recommended: **Manage Messages** for cleanup

**Channel Setup Recommendations:**
- Use dedicated logging channels
- Restrict access to administrators only
- Set up channel topics explaining log purpose
- Consider channel slowmode for high-volume logs

## 📈 Monitoring Dashboard

### Real-time Monitoring

**Live Activity Tracking:**
- Current active users
- Commands per minute/hour
- DM volume monitoring
- Event frequency tracking

**Alert Systems:**
- Unusual activity spikes
- Error rate increases
- Security event notifications
- System performance alerts

### Historical Analysis

**Trend Analysis:**
- Usage trends over time
- Seasonal activity patterns
- Feature popularity changes
- Community growth metrics

**Performance Metrics:**
- Response time trends
- Error rate patterns
- System resource usage
- User satisfaction indicators

## 🛡️ Privacy and Security

### Privacy Considerations

**Data Protection:**
- Log data stored securely
- Personal information limited
- Message content handling policies
- Data retention guidelines

**Access Controls:**
- Administrator-only log access
- Audit trail for log access
- Secure log transmission
- Encrypted log storage

### Compliance Features

**GDPR Compliance:**
- Right to data deletion
- Data processing transparency
- Consent management
- Data portability options

**Security Standards:**
- Encrypted data transmission
- Secure log storage
- Access logging
- Regular security audits

## 🔧 Advanced Configuration

### Custom Log Formats

**Structured Logging:**
- JSON format for automated processing
- Custom field selection
- Filtered log levels
- Conditional logging rules

**Log Routing:**
- Different events to different channels
- Severity-based routing
- User-based filtering
- Time-based log rotation

### Integration Options

**External Systems:**
- Webhook integration for external services
- API endpoints for custom dashboards
- Database export capabilities
- Third-party monitoring integration

## 📊 Best Practices

### Log Management

**Organization Strategy:**
- Separate channels for different log types
- Clear naming conventions for log channels
- Regular log review and cleanup
- Archive old logs appropriately

**Monitoring Workflow:**
- Daily log review routine
- Weekly trend analysis
- Monthly security audits
- Quarterly system performance reviews

### Performance Optimization

**Efficient Logging:**
- Selective logging to reduce noise
- Log level management
- Batch processing for high volume
- Compression for historical data

**Resource Management:**
- Monitor log channel storage
- Regular cleanup of old logs
- Efficient query mechanisms
- Optimized log formats

## ❓ Troubleshooting

### Common Issues

**Logs Not Appearing:**
- ✅ Check bot has **Send Messages** permission in log channel
- ✅ Verify logging is enabled for the event type
- ✅ Confirm channel is set correctly
- ✅ Check bot can access the designated log channel

**Missing Log Information:**
- ✅ Verify bot has required permissions for event monitoring
- ✅ Check if events occur in channels bot can access
- ✅ Ensure bot role hierarchy allows event detection
- ✅ Confirm logging configuration is correct

**Log Channel Spam:**
- ✅ Implement log level filtering
- ✅ Use separate channels for different log types
- ✅ Set appropriate channel slowmode
- ✅ Consider log aggregation strategies

### Performance Issues

**High Log Volume:**
- ✅ Implement selective logging
- ✅ Use log rotation strategies
- ✅ Consider external log storage
- ✅ Optimize log format for storage

**System Resource Usage:**
- ✅ Monitor memory usage for log processing
- ✅ Implement efficient log queuing
- ✅ Use asynchronous logging operations
- ✅ Regular cleanup of processed logs

---

**Next:** Learn about [Server Stats](server-stats.md) for real-time server monitoring.