import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle as CirclePatch
from matplotlib.colors import hsv_to_rgb
from matplotlib import patheffects  # Correct import for path effects

def draw_concentric_circles():
    # Configuration
    num_circles = 15
    segments = 24
    base_radius = 1.5
    radius_step = 0.8
    center = (0, 0)
    total_numbers = num_circles * segments
    max_inputs = 10
    
    # Planet symbols and properties
    planet_data = {
        'sun': {'symbol': '☉', 'size': 22, 'color': (1, 0.8, 0)},
        'moon': {'symbol': '☽', 'size': 20, 'color': (0.9, 0.9, 1)},
        'mercury': {'symbol': '☿', 'size': 18, 'color': (0.7, 0.7, 0.7)},
        'venus': {'symbol': '♀', 'size': 20, 'color': (0.9, 0.7, 0.9)},
        'earth': {'symbol': '♁', 'size': 18, 'color': (0.2, 0.5, 0.8)},
        'mars': {'symbol': '♂', 'size': 20, 'color': (1, 0.3, 0.2)},
        'jupiter': {'symbol': '♃', 'size': 24, 'color': (0.8, 0.6, 0.4)},
        'saturn': {'symbol': '♄', 'size': 22, 'color': (0.9, 0.8, 0.5)},
        'uranus': {'symbol': '⛢', 'size': 20, 'color': (0.6, 0.8, 0.9)},
        'neptune': {'symbol': '♆', 'size': 20, 'color': (0.2, 0.3, 0.9)},
        'pluto': {'symbol': '♇', 'size': 18, 'color': (0.5, 0.2, 0.5)}
    }
    
    # Get planet-degree pairs from user
    planet_degrees = []
    print(f"Enter up to {max_inputs} planet-degree pairs (e.g., 'sun 15'), or 'done' to finish:")
    
    while len(planet_degrees) < max_inputs:
        user_input = input(f"Enter planet-degree pair {len(planet_degrees)+1} (or 'done'): ").strip().lower()
        if user_input == 'done':
            break
        
        parts = user_input.split()
        if len(parts) != 2:
            print("Please enter in format 'planet degree'")
            continue
            
        planet, degree_str = parts
        if planet not in planet_data:
            print(f"Unknown planet. Choose from: {', '.join(planet_data.keys())}")
            continue
            
        try:
            degree = int(degree_str)
            if not (1 <= degree <= total_numbers):
                print(f"Degree must be between 1 and {total_numbers}")
                continue
                
            if any(d[1] == degree for d in planet_degrees):
                print(f"Degree {degree} is already marked. Please choose another.")
                continue
                
            planet_degrees.append((planet, degree))
        except ValueError:
            print("Please enter a valid degree number")
    
    if not planet_degrees:
        print("No entries provided. Exiting.")
        return
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(16, 16))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Calculate max radius
    max_radius = base_radius + (num_circles - 1) * radius_step
    plt.xlim(-max_radius-1.5, max_radius+1.5)
    plt.ylim(-max_radius-1.5, max_radius+1.5)
    
    # Draw circles and numbers first (background elements)
    current_number = 1
    for circle_idx in range(num_circles):
        radius = base_radius + circle_idx * radius_step
        angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
        
        # Draw the circle
        linewidth = 1.5 if circle_idx == 0 else 0.7
        circle = plt.Circle(center, radius, fill=False, 
                          color='black', linewidth=linewidth, alpha=0.7)
        ax.add_patch(circle)
        
        # Draw radial lines
        for angle in angles:
            x_end = radius * np.cos(angle)
            y_end = radius * np.sin(angle)
            linewidth = 0.5 if circle_idx > 0 else 0.8
            ax.plot([0, x_end], [0, y_end], 'black', 
                   linewidth=linewidth, alpha=0.4)
        
        # Add numbers (make them slightly transparent)
        for i, angle in enumerate(angles):
            text_radius = radius - 0.15 if circle_idx == 0 else radius - 0.2
            x = text_radius * np.cos(angle)
            y = text_radius * np.sin(angle)
            
            fontsize = 10 if circle_idx == 0 else (8 if circle_idx < 7 else 6)
            
            ax.text(x, y, str(current_number), 
                   ha='center', va='center', 
                   fontsize=fontsize, alpha=0.8,
                   bbox=dict(facecolor='white', edgecolor='none', 
                             pad=0.1, alpha=0.6))
            
            current_number += 1
    
    # Now draw planetary markers (foreground elements)
    for planet, degree in planet_degrees:
        # Find which circle and angle this degree is on
        circle_idx = (degree - 1) // segments
        radius = base_radius + circle_idx * radius_step
        angle = 2 * np.pi * ((degree - 1) % segments) / segments
        
        # Get planet properties
        props = planet_data[planet]
        symbol = props['symbol']
        color = props['color']
        size = props['size']
        
        # Calculate position
        mark_x = radius * np.cos(angle)
        mark_y = radius * np.sin(angle)
        
        # Draw connecting line (behind planet symbol)
        ax.plot([0, mark_x], [0, mark_y], 
               color=color, linestyle='-', linewidth=1.5, alpha=0.6, zorder=5)
        
        # Draw the planet symbol (foreground)
        ax.text(mark_x, mark_y, symbol, 
               ha='center', va='center', 
               fontsize=size, color=color, 
               zorder=10, fontweight='bold',
               path_effects=[patheffects.withStroke(linewidth=2, foreground='black')])
        
        # Add degree annotation at edge
        annotation_radius = max_radius + 0.8
        annot_x = annotation_radius * np.cos(angle)
        annot_y = annotation_radius * np.sin(angle)
        
        ax.text(annot_x, annot_y, f"{degree}°", 
               ha='center', va='center', 
               color='white', fontsize=10, zorder=10,
               bbox=dict(facecolor=color, edgecolor='black', 
                         pad=2, alpha=0.9))
    
    # Create legend outside the wheel
    legend_elements = [
        plt.Line2D([0], [0], marker='$'+planet_data[p]['symbol']+'$', color='w',
                  label=f'{p.title()} ({d}°)', 
                  markerfacecolor=planet_data[p]['color'],
                  markersize=15, markeredgecolor='black', markeredgewidth=1)
        for p, d in planet_degrees
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', 
             title="Planetary Positions", fontsize=10,
             bbox_to_anchor=(1.02, 1), borderaxespad=0.)
    
    plt.title('Planetary Positions on Zodiac Wheel', pad=20, fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(right=0.82)  # Make space for legend
    plt.show()

if __name__ == "__main__":
    draw_concentric_circles()