# Server Stats

Real-time server monitoring and statistics display with auto-updating embeds and comprehensive server analytics.

## 📊 Overview

The Sprouts server stats system provides dynamic, real-time monitoring of server statistics with beautiful auto-updating embeds that keep your community informed about server growth and activity.

### Key Features

- **📈 Real-time Statistics** - Live updating member counts and server data
- **🎨 Auto-updating Embeds** - Beautiful displays that refresh automatically
- **📊 Growth Tracking** - Historical data and trend analysis
- **⚙️ Easy Management** - Simple setup and configuration
- **🔄 Reliable Updates** - Consistent data refresh and error handling

## 🚀 Setting Up Server Stats

### Initialize Server Stats

```
s.serverstats start
```

Begins monitoring the current server and creates auto-updating stat embeds.

### Display Current Statistics

```
s.serverstats show
```

Shows current server statistics without setting up monitoring:
- **Member Count** - Total server members
- **Online Members** - Currently active users  
- **Bot Count** - Number of bots in server
- **Channel Statistics** - Text, voice, and category counts
- **Role Information** - Total roles and hierarchy

### Stop Server Monitoring

```
s.serverstats stop
```

Stops automatic server statistics monitoring and removes auto-updating embeds.

### List Monitored Servers

```
s.serverstats list
```

Shows all servers currently being monitored with their statistics.

## 📈 Statistics Displayed

### Member Statistics

**Total Members:**
- All server members including bots
- Real-time count updates
- Growth tracking over time
- Member join/leave rate

**Online Status:**
- Currently online members
- Away/idle member count
- Do not disturb users
- Offline member tracking

**Bot Analytics:**
- Total bot count in server
- Bot-to-human ratio
- Active vs inactive bots
- Bot permission analysis

### Server Information

**Channel Breakdown:**
- Text channel count
- Voice channel count
- Category organization
- Total channel count

**Role Analytics:**
- Total role count
- Permission distribution
- Role hierarchy depth
- Custom role usage

**Server Features:**
- Boost level and count
- Verification level
- Server features enabled
- Premium subscriber count

### Growth Metrics

**Historical Data:**
- Member growth over time
- Peak online times
- Activity patterns
- Seasonal trends

**Engagement Metrics:**
- Average online percentage
- Activity level indicators
- Community health scores
- Engagement trend analysis

## 🎨 Display Customization

### Auto-updating Embeds

**Real-time Updates:**
- Statistics refresh every few minutes
- Smooth data transitions
- Error-resistant updating
- Consistent formatting

**Visual Design:**
- Clean, professional appearance
- Color-coded statistics
- Progress bars for visual data
- Custom emoji integration

### Embed Content

**Default Statistics Display:**
```
📊 Server Statistics
👥 Total Members: 1,234 (↑ 15 today)
🟢 Online Now: 456 (37% of total)  
🤖 Bots: 23 (1.9% of total)
📈 Growth: +142 this week

📁 Channels
💬 Text: 25 channels
🔊 Voice: 8 channels
📂 Categories: 6 categories

🎭 Roles: 18 total roles
💎 Boost Level: 2 (12 boosts)
```

## ⚙️ Management Commands

### Server Requirements

**Permissions Needed:**
- **Manage Guild** permission required to start/stop monitoring
- **Send Messages** permission for displaying statistics
- **Embed Links** permission for formatted displays
- **Read Message History** for context and updates

### Monitoring Status

**Active Monitoring Indicators:**
- Auto-updating embed presence
- Regular refresh timestamps
- Status indicators in embed footer
- Error notifications if updates fail

**Health Monitoring:**
- Update frequency tracking
- Error rate monitoring
- Performance metrics
- System resource usage

## 📊 Advanced Analytics

### Trend Analysis

**Growth Patterns:**
- Daily member change rates
- Weekly growth averages
- Monthly trend analysis
- Seasonal activity patterns

**Activity Insights:**
- Peak online hours
- Low activity periods
- Weekend vs weekday patterns
- Holiday impact analysis

### Comparative Analytics

**Server Benchmarks:**
- Size category comparisons
- Growth rate rankings
- Activity level assessments
- Community health indicators

**Performance Metrics:**
- Member retention rates
- Engagement percentages
- Activity consistency scores
- Community vitality index

## 🔧 Technical Implementation

### Update Mechanisms

**Refresh Strategy:**
- Intelligent update scheduling
- Delta-based change detection
- Batch processing for efficiency
- Error recovery mechanisms

**Data Sources:**
- Discord API integration
- Real-time event processing
- Cached data optimization
- Historical data storage

### Performance Optimization

**Efficient Processing:**
- Minimal API calls
- Smart caching strategies
- Batch update processing
- Resource usage optimization

**Scalability Features:**
- Multi-server monitoring
- Load balancing capabilities
- Database optimization
- Memory management

## 🎯 Best Practices

### Effective Usage

**Strategic Placement:**
- Use in main information channels
- Consider member visibility
- Avoid high-traffic spam channels
- Include in server welcome areas

**Community Engagement:**
- Celebrate member milestones
- Highlight growth achievements
- Share interesting statistics
- Use data for community planning

### Maintenance Considerations

**Regular Monitoring:**
- Check update consistency
- Verify statistical accuracy
- Monitor for display errors
- Review performance impact

**Community Communication:**
- Explain statistics to members
- Celebrate growth milestones
- Address any concerns about data
- Provide context for fluctuations

## 📈 Growth Milestone Features

### Automatic Celebrations

**Member Milestones:**
- 100, 500, 1000+ member celebrations
- Custom milestone notifications
- Community achievement announcements
- Growth rate acknowledgments

**Achievement Tracking:**
- First 100 members milestone
- Rapid growth achievements
- Consistency awards
- Community building success

### Community Building

**Engagement Strategies:**
- Use statistics to motivate growth
- Share interesting growth trends
- Celebrate community achievements
- Encourage member recruitment

## 🔍 Troubleshooting

### Common Issues

**Statistics Not Updating:**
- ✅ Check bot has **Manage Guild** permission
- ✅ Verify embed is in accessible channel
- ✅ Confirm bot has **Send Messages** permission
- ✅ Ensure monitoring is active: `s.serverstats show`

**Incorrect Data Display:**
- ✅ Allow time for Discord cache updates
- ✅ Check for recent server changes
- ✅ Verify bot can access all server areas
- ✅ Restart monitoring if persistent: stop then start

**Update Frequency Issues:**
- ✅ Monitor for API rate limits
- ✅ Check system resource availability
- ✅ Verify network connectivity
- ✅ Review error logs for patterns

**Display Formatting Problems:**
- ✅ Ensure bot has **Embed Links** permission
- ✅ Check channel message limits
- ✅ Verify embed content size
- ✅ Confirm custom emoji accessibility

### Performance Optimization

**Resource Management:**
- Monitor CPU usage during updates
- Check memory consumption patterns
- Optimize update frequency
- Implement efficient data storage

**Network Optimization:**
- Minimize redundant API calls
- Use efficient data retrieval methods
- Implement proper caching strategies
- Optimize embed update processes

## 💡 Creative Usage Ideas

### Community Engagement

**Growth Competitions:**
- Set member recruitment goals
- Celebrate growth milestones
- Create friendly server competitions
- Reward active community builders

**Data Storytelling:**
- Share interesting growth trends
- Highlight peak activity times
- Explain seasonal patterns
- Use statistics for planning events

### Administrative Insights

**Server Health Monitoring:**
- Track member retention
- Monitor activity levels
- Identify growth opportunities
- Plan capacity expansions

**Community Analysis:**
- Understand member behavior
- Identify popular times
- Plan event scheduling
- Optimize server structure

## 📋 Statistical Categories

### Core Metrics

**Essential Statistics:**
- Total member count with growth indicators
- Online member percentage and trends
- Bot count and bot-to-human ratio
- Channel distribution and organization

**Growth Indicators:**
- Daily change rates (+/- members)
- Weekly growth patterns
- Monthly trend analysis
- Historical growth comparison

### Advanced Metrics

**Engagement Analysis:**
- Average online percentage
- Peak activity time identification
- Member activity consistency
- Community health indicators

**Server Optimization:**
- Channel utilization rates
- Role distribution analysis
- Permission optimization insights
- Server feature usage statistics

---

**Next:** Learn about [Developer Commands](developer-commands.md) for advanced bot management.