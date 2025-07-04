import matplotlib.pyplot as plt
import numpy as np

def draw_concentric_circles():
    # Configuration
    num_circles = 15
    segments = 24
    base_radius = 1.5  # Larger starting radius
    radius_step = 0.8  # Smaller step between circles
    center = (0, 0)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(16, 16))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Calculate max radius for proper scaling
    max_radius = base_radius + (num_circles - 1) * radius_step
    plt.xlim(-max_radius-1, max_radius+1)
    plt.ylim(-max_radius-1, max_radius+1)
    
    # Draw circles and numbers
    current_number = 1
    for circle_idx in range(num_circles):
        radius = base_radius + circle_idx * radius_step
        angles = np.linspace(0, 2*np.pi, segments, endpoint=False)
        
        # Draw the circle with varying linewidth
        linewidth = 1.5 if circle_idx == 0 else 0.7  # Thicker line for first circle
        circle = plt.Circle(center, radius, fill=False, 
                          color='black', linewidth=linewidth)
        ax.add_patch(circle)
        
        # Draw radial lines for segments
        for angle in angles:
            x_end = radius * np.cos(angle)
            y_end = radius * np.sin(angle)
            linewidth = 0.5 if circle_idx > 0 else 0.8  # Thicker for first circle
            ax.plot([0, x_end], [0, y_end], 'black', 
                   linewidth=linewidth, alpha=0.7)
        
        # Add numbers with larger font for first circle
        for i, angle in enumerate(angles):
            # Position the number slightly inside the circle
            text_radius = radius - 0.15 if circle_idx == 0 else radius - 0.2
            x = text_radius * np.cos(angle)
            y = text_radius * np.sin(angle)
            
            fontsize = 10 #if circle_idx == 0 else (8 if circle_idx < 7 else 6)
            
            ax.text(x, y, str(current_number), 
                   ha='center', va='center', 
                   fontsize=fontsize,
                   bbox=dict(facecolor='white', edgecolor='none', 
                             pad=0.1, alpha=0.8))
            current_number += 1
    
    plt.title(f'Concentric Circles: {num_circles} circles, {segments} segments each (1-{num_circles*segments})', 
             pad=20, fontsize=12)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_concentric_circles()