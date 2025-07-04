import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle as CirclePatch
from matplotlib.colors import hsv_to_rgb

def draw_concentric_circles():
    # Configuration
    num_circles = 15
    segments = 24
    base_radius = 1.5
    radius_step = 0.8
    center = (0, 0)
    total_numbers = num_circles * segments
    max_inputs = 10
    
    # Planet symbols dictionary
    planet_symbols = {
        'sun': '☉',
        'moon': '☽',
        'mercury': '☿',
        'venus': '♀',
        'earth': '♁',
        'mars': '♂',
        'jupiter': '♃',
        'saturn': '♄',
        'uranus': '⛢',
        'neptune': '♆',
        'pluto': '♇'
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
        if planet not in planet_symbols:
            print(f"Unknown planet. Choose from: {', '.join(planet_symbols.keys())}")
            continue
            
        try:
            degree = int(degree_str)
            if not (1 <= degree <= total_numbers):
                print(f"Degree must be between 1 and {total_numbers}")
                continue
                
            # Check if degree is already taken
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
    plt.xlim(-max_radius-1, max_radius+1)
    plt.ylim(-max_radius-1, max_radius+1)
    
    # Generate distinct colors for each planet
    colors = [hsv_to_rgb([i/len(planet_degrees), 0.8, 0.8]) for i in range(len(planet_degrees))]
    
    # Draw circles and numbers
    current_number = 1
    for circle_idx in range(num_circles):
        radius = base_radius + circle_idx * radius_step
        angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
        
        # Draw the circle
        linewidth = 1.5 if circle_idx == 0 else 0.7
        circle = plt.Circle(center, radius, fill=False, 
                          color='black', linewidth=linewidth)
        ax.add_patch(circle)
        
        # Draw radial lines
        for angle in angles:
            x_end = radius * np.cos(angle)
            y_end = radius * np.sin(angle)
            linewidth = 0.5 if circle_idx > 0 else 0.8
            ax.plot([0, x_end], [0, y_end], 'black', 
                   linewidth=linewidth, alpha=0.7)
        
        # Add numbers
        for i, angle in enumerate(angles):
            text_radius = radius - 0.15 if circle_idx == 0 else radius - 0.2
            x = text_radius * np.cos(angle)
            y = text_radius * np.sin(angle)
            
            fontsize = 10 if circle_idx == 0 else (8 if circle_idx < 7 else 6)
            
            ax.text(x, y, str(current_number), 
                   ha='center', va='center', 
                   fontsize=fontsize,
                   bbox=dict(facecolor='white', edgecolor='none', 
                             pad=0.1, alpha=0.8))
            
            # Check if this number should be marked
            for idx, (planet, degree) in enumerate(planet_degrees):
                if current_number == degree:
                    color = colors[idx]
                    symbol = planet_symbols[planet]
                    
                    # Calculate position at the circle's edge
                    mark_radius = radius
                    mark_x = mark_radius * np.cos(angle)
                    mark_y = mark_radius * np.sin(angle)
                    
                    # Add a colored symbol
                    ax.text(mark_x, mark_y, symbol, 
                           ha='center', va='center', 
                           fontsize=16, color=color, zorder=10)
                    
                    # Add connecting line from center
                    ax.plot([0, mark_x], [0, mark_y], 
                           color=color, linestyle='--', linewidth=1, alpha=0.5)
                    
                    # Add annotation with planet name
                    ax.annotate(f'{planet.title()} ({degree})',
                               xy=(mark_x, mark_y),
                               xytext=(mark_x*1.2, mark_y*1.2),
                               arrowprops=dict(arrowstyle="->", color=color),
                               color=color, fontsize=14)
            
            current_number += 1
    
    # Create legend
    legend_elements = [
        plt.Line2D([0], [0], marker='$'+planet_symbols[p]+'$', color='w', 
                  label=f'{p.title()} ({d})', markerfacecolor=colors[i], 
                  markersize=15, markeredgecolor=colors[i])
        for i, (p, d) in enumerate(planet_degrees)
    ]
    ax.legend(handles=legend_elements, loc='upper right', 
             title="Planetary Positions", fontsize=10)
    
    plt.title(f'Planetary Positions on Concentric Circles (1-{total_numbers})', 
             pad=20, fontsize=14)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_concentric_circles()