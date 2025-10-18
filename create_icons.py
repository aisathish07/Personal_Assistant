# create_icons.py - Generate icons for Jarvis Assistant
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

def create_jarvis_icon(size=256, output_path="assets/jarvis.png"):
    """Create a modern Jarvis icon"""
    
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate sizes
    center = size // 2
    outer_radius = int(size * 0.45)
    middle_radius = int(size * 0.35)
    inner_radius = int(size * 0.15)
    
    # Draw outer glow (gradient effect)
    for i in range(20):
        alpha = int(50 - (i * 2.5))
        glow_radius = outer_radius + (i * 2)
        draw.ellipse(
            [center - glow_radius, center - glow_radius,
             center + glow_radius, center + glow_radius],
            fill=(0, 255, 191, alpha)
        )
    
    # Draw outer circle (main border)
    draw.ellipse(
        [center - outer_radius, center - outer_radius,
         center + outer_radius, center + outer_radius],
        fill=(26, 26, 46),
        outline=(0, 255, 191),
        width=6
    )
    
    # Draw middle circle (secondary ring)
    draw.ellipse(
        [center - middle_radius, center - middle_radius,
         center + middle_radius, center + middle_radius],
        fill=(26, 26, 46),
        outline=(0, 191, 255),
        width=4
    )
    
    # Draw inner circle (core)
    draw.ellipse(
        [center - inner_radius, center - inner_radius,
         center + inner_radius, center + inner_radius],
        fill=(0, 255, 191)
    )
    
    # Add "J" letter
    try:
        font = ImageFont.truetype("arial.ttf", size // 3)
    except:
        font = ImageFont.load_default()
    
    text = "J"
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    draw.text(
        (center - text_width // 2, center - text_height // 2 - 5),
        text,
        fill=(0, 255, 191),
        font=font
    )
    
    return img

def create_icon_set():
    """Create a complete icon set"""
    
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    print("🎨 Creating Jarvis icon set...")
    
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    for size in sizes:
        print(f"  Creating {size}x{size}...")
        icon = create_jarvis_icon(size)
        icon.save(assets_dir / f"jarvis_{size}.png")
    
    # Create main icon
    print("  Creating main icon...")
    main_icon = create_jarvis_icon(256)
    main_icon.save(assets_dir / "jarvis.png")
    
    # Create ICO file (Windows)
    print("  Creating Windows .ico file...")
    try:
        # Create multi-resolution ICO
        ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icons = [create_jarvis_icon(s[0]) for s in ico_sizes]
        icons[0].save(
            assets_dir / "jarvis.ico",
            format='ICO',
            sizes=ico_sizes
        )
        print("  ✅ jarvis.ico created")
    except Exception as e:
        print(f"  ⚠️  ICO creation failed: {e}")
        print("     Using PNG as fallback")
    
    # Create system tray icons (different states)
    print("  Creating state icons...")
    
    states = {
        "idle": (0, 255, 191),      # Cyan
        "listening": (0, 191, 255),  # Blue
        "speaking": (0, 255, 136),   # Green
        "thinking": (255, 191, 0),   # Amber
        "error": (255, 0, 0)         # Red
    }
    
    for state, color in states.items():
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Outer circle
        draw.ellipse([8, 8, 56, 56], fill=(26, 26, 46), outline=color, width=3)
        
        # Inner circle
        draw.ellipse([20, 20, 44, 44], fill=color)
        
        img.save(assets_dir / f"tray_{state}.png")
    
    print("  ✅ State icons created")
    
    # Create banner
    print("  Creating banner...")
    banner = Image.new('RGBA', (1200, 300), (26, 26, 46))
    draw = ImageDraw.Draw(banner)
    
    # Add large icon
    large_icon = create_jarvis_icon(200)
    banner.paste(large_icon, (50, 50), large_icon)
    
    # Add text
    try:
        title_font = ImageFont.truetype("arial.ttf", 80)
        subtitle_font = ImageFont.truetype("arial.ttf", 30)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    draw.text((300, 80), "JARVIS", fill=(0, 255, 191), font=title_font)
    draw.text((300, 180), "Your Personal AI Assistant", fill=(255, 255, 255), font=subtitle_font)
    
    banner.save(assets_dir / "jarvis_banner.png")
    print("  ✅ Banner created")
    
    print("\n✅ Icon set complete!")
    print(f"📁 Files saved to: {assets_dir.absolute()}")
    print("\nCreated files:")
    for f in sorted(assets_dir.glob("*")):
        print(f"  - {f.name}")

def create_loading_animation():
    """Create loading animation frames"""
    
    assets_dir = Path("assets") / "loading"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n🎬 Creating loading animation...")
    
    frames = 12
    size = 128
    
    for frame in range(frames):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        radius = 40
        
        # Rotating arc
        angle = (frame / frames) * 360
        draw.arc(
            [center - radius, center - radius, center + radius, center + radius],
            start=angle,
            end=angle + 270,
            fill=(0, 255, 191),
            width=6
        )
        
        # Center dot
        draw.ellipse([center - 8, center - 8, center + 8, center + 8], fill=(0, 255, 191))
        
        img.save(assets_dir / f"loading_{frame:02d}.png")
    
    print(f"✅ Created {frames} loading frames")

if __name__ == "__main__":
    print("=" * 50)
    print("  JARVIS ICON CREATOR")
    print("=" * 50)
    print()
    
    create_icon_set()
    create_loading_animation()
    
    print("\n" + "=" * 50)
    print("  DONE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Check the 'assets' folder for all generated icons")
    print("2. Use jarvis.ico for PyInstaller: --icon=assets/jarvis.ico")
    print("3. The banner can be used in README.md")
    print()