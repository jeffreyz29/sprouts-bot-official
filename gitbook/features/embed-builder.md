# Embed Builder

Create stunning Discord embeds with live preview, dropdown menus, and powerful customization options.

## 🎨 Overview

The Sprouts embed builder provides a user-friendly interface for creating professional Discord embeds without any coding knowledge. Perfect for announcements, server information, ticket responses, and more.

### Key Features

- **🔄 Live Preview** - See changes as you make them
- **📋 Dropdown Menus** - Easy field selection and editing
- **🎨 Color Picker** - Visual color selection with presets
- **💾 Template System** - Save and reuse your favorite designs
- **🔗 Variable Support** - Dynamic content with server variables
- **📱 Mobile Friendly** - Works perfectly on mobile Discord

## 🚀 Getting Started

### Launch the Embed Builder

```
s.embedcreate [name]
```

This opens the interactive embed builder interface with:

#### 🎛️ Main Control Panel
- **Live Embed Preview** - Real-time preview of your embed
- **Edit Dropdown Menu** - Select what to modify
- **Action Buttons** - Save, post, or cancel
- **Quick Templates** - Access to saved designs

#### 🎨 Editing Options
- **Title** - Main embed heading
- **Description** - Primary content area
- **Color** - Border and accent color
- **Fields** - Structured information blocks
- **Footer** - Bottom text and icon
- **Author** - Top section with name and icon
- **Thumbnail** - Small image (top-right)
- **Image** - Large image (bottom)
- **URL** - Make embed clickable

## 📝 Creating Your First Embed

### Step 1: Set Basic Information

1. **Choose "Title"** from dropdown
2. **Enter your title** (up to 256 characters)
3. **Watch live preview** update automatically

```
Example: "🌟 Welcome to Our Server!"
```

### Step 2: Add Description

1. **Select "Description"** from dropdown
2. **Write your main content** (up to 4096 characters)
3. **Use Discord markdown** for formatting

```markdown
Example:
Welcome to **Our Amazing Server**! 

We're excited to have you here. Please:
• Read the rules in <#rules>
• Introduce yourself in <#introductions>  
• Have fun and be respectful!

*Enjoy your stay!* 🎉
```

### Step 3: Choose Colors

1. **Select "Color"** from dropdown
2. **Pick from presets** or enter hex code
3. **See instant preview** of color change

Popular color presets:
- 🟢 **Green** (`0x2ecc71`) - Success, positive
- 🔴 **Red** (`0xe74c3c`) - Errors, warnings
- 🔵 **Blue** (`0x3498db`) - Information, neutral
- 🟡 **Yellow** (`0xf1c40f`) - Attention, highlights
- 🟣 **Purple** (`0x9b59b6`) - Special, premium

### Step 4: Add Structured Fields

Fields create organized information blocks:

1. **Select "Add Field"** from dropdown  
2. **Enter field name** (up to 256 characters)
3. **Add field value** (up to 1024 characters)
4. **Choose inline option** (side-by-side vs stacked)

```
Example Fields:
Name: "📋 Server Rules"
Value: "1. Be respectful\n2. No spam\n3. Use appropriate channels"
Inline: No

Name: "🎮 Gaming"  
Value: "We play Minecraft, Valorant, and more!"
Inline: Yes

Name: "🎵 Music"
Value: "Daily music sessions at 8 PM EST"
Inline: Yes
```

## 🎛️ Advanced Features

### Footer Customization

Add footer text and icons:

1. **Select "Footer Text"** - Bottom text (up to 2048 chars)
2. **Select "Footer Icon"** - Small icon next to text

```
Example:
Footer Text: "Created by ModTeam • Last updated March 2024"
Footer Icon: https://example.com/server-icon.png
```

### Author Section

Create a professional header:

1. **Select "Author Name"** - Name at the top
2. **Select "Author Icon"** - Small icon next to name  
3. **Select "Author URL"** - Make name clickable

```
Example:
Author Name: "Server Announcement"
Author Icon: https://example.com/admin-icon.png
Author URL: https://yourserver.com/announcements
```

### Images and Media

Add visual elements:

1. **Thumbnail** - Small image (top-right corner)
   - Best size: 128x128px
   - Supports: PNG, JPG, GIF, WEBP

2. **Large Image** - Full-width image at bottom
   - Max size: 2048x2048px
   - Displays below all other content

### Clickable Embeds

Make entire embed clickable:

1. **Select "URL"** from dropdown
2. **Enter destination link**
3. **Embed title becomes clickable**

Perfect for:
- **📢 Announcements** linking to full posts
- **🎫 Ticket Systems** linking to forms
- **📊 Statistics** linking to dashboards
- **🎮 Events** linking to registration

## 💾 Template System

### Saving Embeds

Save your creations for reuse:

1. **Click "Save Embed"** button in the interface
2. **Enter template name** (unique identifier)
3. **Confirm save** - appears in template list

Or create embeds directly:
```
s.embedcreate welcome     # Create new embed named "welcome"
s.embedcreateempty rules  # Create blank embed template
```

### Using Saved Embeds

Load previously saved templates:

```
s.embedview <name>       # Preview saved embed
s.embededit <name>       # Edit existing embed
s.embedlist             # View all saved embeds
```

### Template Management

```
s.embeddelete <name>    # Delete saved embed
s.embedexport <name>    # Export embed as YAML file
s.embedimport [name]    # Import embed from YAML file
s.embedoldedit <name>   # Use legacy text editor
```

### Popular Template Ideas

**Welcome Message:**
- Server introduction
- Rules summary  
- Channel guide
- Role information

**Announcement Template:**
- Event notifications
- Update announcements
- Important news
- Maintenance notices

**Ticket Response:**
- Common solutions
- FAQ answers
- Escalation procedures
- Thank you messages

**Server Info:**
- Statistics display
- Staff listings
- Feature highlights
- Contact information

## 🔗 Variable Support

### Dynamic Content

Use variables for personalized content:

```
Available Variables:
{user}           - User mention
{user.name}      - Username  
{user.id}        - User ID
{server}         - Server name
{server.members} - Member count
{channel}        - Current channel
{date}           - Current date
{time}           - Current time
```

### Variable Examples

```markdown
**Welcome {user.name}!**

You're member #{server.members} in **{server}**!

Please introduce yourself in {channel} and read our rules.

*Joined on {date} at {time}*
```

### Advanced Variables

```
{server.owner}     - Server owner mention
{server.created}   - Server creation date  
{server.boost}     - Boost level
{server.channels}  - Channel count
{server.roles}     - Role count
{user.joined}      - User join date
{user.avatar}      - User avatar URL
```

## 🎨 Design Best Practices

### Color Psychology

- **🟢 Green** - Success, growth, positive actions
- **🔴 Red** - Errors, urgency, important warnings  
- **🔵 Blue** - Trust, stability, information
- **🟡 Yellow** - Attention, caution, highlights
- **🟣 Purple** - Premium, special, creative
- **⚫ Black** - Elegant, formal, serious
- **⚪ White** - Clean, minimal, simple

### Text Formatting

Use Discord markdown for rich text:

```markdown
**Bold text**           - Strong emphasis
*Italic text*           - Light emphasis  
__Underline text__      - Additional emphasis
~~Strikethrough~~       - Crossed out text
`Code text`             - Inline code
```Code block```        - Multi-line code
> Quote text            - Indented quote
```

### Content Organization

**Hierarchy Guidelines:**
1. **Title** - Main topic (short, descriptive)
2. **Description** - Key information (clear, concise)
3. **Fields** - Supporting details (organized, scannable)
4. **Footer** - Meta information (timestamps, credits)

**Field Best Practices:**
- **Use inline fields** for related info (2-3 per row)
- **Use non-inline fields** for detailed explanations
- **Keep field names short** and descriptive
- **Organize logically** from most to least important

## 📱 Mobile Optimization

### Mobile-Friendly Design

Consider mobile users (60%+ of Discord users):

- **Short titles** - Avoid truncation
- **Concise descriptions** - Reduce scrolling
- **Minimal fields** - Prevent overcrowding  
- **Clear hierarchy** - Easy to scan
- **Readable fonts** - Avoid tiny text

### Testing on Mobile

Always test your embeds on mobile:
1. **Preview in Discord mobile app**
2. **Check text readability**
3. **Verify image sizing**
4. **Test field layout**
5. **Confirm button accessibility**

## 🔧 Integration Examples

### Ticket System Integration

Create ticket response templates:

```
s.embedcreate ticket-faq
# Design helpful response in the editor
# Save through the interface
s.ticketuseembed ticket-faq
```

### Auto Responder Integration

Auto responders use text responses, but you can reference saved embeds in responses:

```
s.autoresponder add trigger:rules reply:Please check our server rules!
s.autoresponder add trigger:help reply:Use s.embedview help-guide for assistance
```

### Sticky Message Integration

Sticky messages use text content:

```
s.embedcreate server-info
# Design server info embed and save
# Then reference in sticky messages
s.stick Check out our server info with: s.embedview server-info
```

## 📊 Analytics & Optimization

### Embed Performance

Track how users interact with your embeds:
- **👆 Click-through rates** - URL clicks
- **👀 View duration** - Time spent reading
- **💬 Response rates** - Messages after embed
- **🔄 Share frequency** - Embed sharing

### A/B Testing

Test different designs:
1. **Create variations** with different colors/layouts
2. **Post in different channels** or times
3. **Monitor engagement** and feedback
4. **Iterate based on results**

## ❓ Troubleshooting

### Common Issues

**Embed not displaying:**
- ✅ Check bot has **Embed Links** permission
- ✅ Verify embed isn't empty (needs title OR description)
- ✅ Ensure color code is valid hex format

**Images not showing:**
- ✅ Use direct image URLs (ending in .png, .jpg, etc.)
- ✅ Ensure images are publicly accessible
- ✅ Check image size limits (8MB max)
- ✅ Use HTTPS URLs for security

**Fields cut off:**
- ✅ Keep field names under 256 characters
- ✅ Keep field values under 1024 characters
- ✅ Total embed size under 6000 characters

**Variables not working:**
- ✅ Use exact variable syntax: `{variable}`
- ✅ Check variable is available in current context
- ✅ Verify spelling and capitalization

### Getting Help

Need assistance with embed creation?
- **📚 Examples** - Check template gallery
- **🎨 Design Help** - Join design discussions
- **🔧 Technical Support** - Report bugs or issues
- **💡 Feature Requests** - Suggest improvements

---

**Next:** Learn about [Auto Responders](auto-responders.md) to automate your embed responses.