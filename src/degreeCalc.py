import ephem
import datetime
import math
import csv

# Function to find new moons in a specific year
def get_new_moons(year):
    new_moons = []
    date = datetime.date(year, 1, 1)
    end_date = datetime.date(year + 1, 1, 1)
    while date < end_date:
        next_new_moon = ephem.next_new_moon(date.strftime('%Y-%m-%d'))
        if next_new_moon.datetime().year == year:
            new_moons.append(next_new_moon)
        date = next_new_moon.datetime().date() + datetime.timedelta(days=1)
    return new_moons

# Function to determine the astrological sign based on ecliptic longitude
def get_astrological_sign(longitude):
    signs = [
        ('Aries', 0, 30),
        ('Taurus', 30, 60),
        ('Gemini', 60, 90),
        ('Cancer', 90, 120),
        ('Leo', 120, 150),
        ('Virgo', 150, 180),
        ('Libra', 180, 210),
        ('Scorpio', 210, 240),
        ('Sagittarius', 240, 270),
        ('Capricorn', 270, 300),
        ('Aquarius', 300, 330),
        ('Pisces', 330, 360),
    ]
    for sign, start, end in signs:
        if start <= longitude < end:
            return sign
    return None

# Function to calculate information for a given degree from the new moon
def calculate_info_from_new_moon(new_moon_date, new_moon_longitude, input_degree):
    #degrees_per_day = 12.19  # Average degrees the moon moves per day
    degrees_per_day = 13.1764
    days_needed = input_degree / degrees_per_day
    calculated_date = new_moon_date + datetime.timedelta(days=days_needed)
    calculated_moon = ephem.Moon(calculated_date)
    calculated_moon.compute(calculated_date)
    calculated_longitude = float(ephem.Ecliptic(calculated_moon).lon) * 180 / math.pi
    calculated_sign = get_astrological_sign(calculated_longitude)
    calculated_degree = calculated_longitude % 30
    return calculated_date, calculated_sign, calculated_degree

# Function to print new moon information for a given year and write to CSV
def print_new_moon_info(year):
    new_moons = get_new_moons(year)
    #with open('new_moon_data.csv', mode='w', newline='') as file:
    #    writer = csv.writer(file)
        #writer.writerow(['New Moon Data', 'Degree Data'])
        
    for moon in new_moons:
        moon_date_utc = moon.datetime()
        moon_obj = ephem.Moon(moon_date_utc)
        moon_obj.compute(moon_date_utc)
        ecliptic_longitude = float(ephem.Ecliptic(moon_obj).lon) * 180 / math.pi
        sign = get_astrological_sign(ecliptic_longitude)
        degree = ecliptic_longitude % 30
        new_moon_info = f"New Moon on {moon_date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} in {sign}, at {degree:.2f}°"
        print(new_moon_info)
   #     writer.writerow([new_moon_info, f"{degree:.2f}° in {sign}"])

# Function to get information for a specific degree input by the user and write to CSV
def get_info_for_user_degree(year, input_degree):
    new_moons = get_new_moons(year)
    with open('new_moon_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        for moon in new_moons:
            moon_date_utc = moon.datetime()
            # print(f"Debug: New Moon Date (UTC) = {moon_date_utc}")
            moon_obj = ephem.Moon(moon_date_utc)
            moon_obj.compute(moon_date_utc)
            ecliptic_longitude = float(ephem.Ecliptic(moon_obj).lon) * 180 / math.pi
            # print(f"Debug: Ecliptic Longitude = {ecliptic_longitude}")
            sign = get_astrological_sign(ecliptic_longitude)
            degree = ecliptic_longitude % 30
            # print(f"Debug: Sign = {sign}, Degree = {degree}")
            calculated_date, calculated_sign, calculated_degree = calculate_info_from_new_moon(moon_date_utc, ecliptic_longitude, input_degree)
            cst_offset = datetime.timedelta(hours=-6)
            cst_degree_date = calculated_date + cst_offset
            frm_degree_date = cst_degree_date.strftime('%d-%m-%Y %H:%M:%S CST')
            cst_moondate = moon_date_utc + cst_offset
            frm_moondate = cst_moondate.strftime('%d-%m-%Y %H:%M:%S CST')
           # print("CST", formatted_date)
            # print(f"Debug: Calculated Date = {calculated_date}, Calculated Sign = {calculated_sign}, Calculated Degree = {calculated_degree}")
            #degree_info = f"Degree {input_degree} on {calculated_date.strftime('%Y-%m-%d %H:%M:%S UTC')} in {calculated_sign}, at {calculated_degree:.2f}°"
            #print(degree_info)
            #writer.writerow([f"New Moon on {moon_date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} in {sign}, at {degree:.2f}°", degree_info])
            #print(f"Debug: Calculated Date = {formatted_date}, Calculated Sign = {calculated_sign}, Calculated Degree = {calculated_degree}")
            degree_info = input_degree,frm_degree_date,f"{calculated_sign} {calculated_degree:.2f}°"
            print(degree_info)
            #writer.writerow([frm_moondate,f"{sign} {degree:.2f}°", degree_info])
            writer.writerow([frm_moondate,f"{sign} {degree:.2f}°",input_degree,frm_degree_date,f"{calculated_sign} {calculated_degree:.2f}°"])

# Example usage
#year = int(input("Enter year to calculate new moons: "))
#print_new_moon_info(year)

#input_degree = int(input("Enter degree to find information for: "))
#get_info_for_user_degree(year, input_degree)

# Function to get exact time and date for a specific year, month, sign, and degree input by the user
def get_exact_time_for_degree():
    year = int(input("Enter year: "))
    month = int(input("Enter month (1-12): "))
    sign_options = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]
    print("Select sign:")
    for i, sign in enumerate(sign_options, 1):
        print(f"{i}. {sign}")
    sign_index = int(input("Enter the number corresponding to the sign (1-12): "))
    input_sign = sign_options[sign_index - 1]
    input_degree = int(input("Enter degree (0-29): "))
    
    date = datetime.datetime(year, month, 1, 0, 0)
    end_date = datetime.datetime(year, month + 1, 1, 0, 0) if month < 12 else datetime.datetime(year + 1, 1, 1, 0, 0)
    found = False
    while date < end_date:
        moon = ephem.Moon(date)
        moon.compute(date)
        ecliptic_longitude = float(ephem.Ecliptic(moon).lon) * 180 / math.pi
        sign = get_astrological_sign(ecliptic_longitude)
        degree = ecliptic_longitude % 30
        if sign == input_sign and int(degree) == input_degree:
            cst_offset = datetime.timedelta(hours=-6)
            cst_date = date + cst_offset
            frm_cst_date = cst_date.strftime('%d-%m-%Y %H:%M:%S CST')
            #print(f"Exact time and date: {date.strftime('%Y-%m-%d %H:%M:%S UTC')} in {sign} at {degree:.2f}°")
            print(f"Exact time and date: {frm_cst_date} in {sign} at {degree:.2f}°")
            found = True
            break
        date += datetime.timedelta(hours=1)
    if not found:
        print("No exact match found within the specified month.")

def find_planetary_aspects(planet1_name, planet2_name, year):
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year + 1, 1, 1)
    current_date = start_date
    aspects = []
    orb = 1.0  # Orb of 1 degree
    valid_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 
                    'Saturn', 'Uranus', 'Neptune', 'Pluto']

    if planet1_name not in valid_planets or planet2_name not in valid_planets:
        print("Invalid planet name. Valid planets are:", ', '.join(valid_planets))
        return []

    while current_date < end_date:
        try:
            dt = datetime.datetime(current_date.year, current_date.month, current_date.day, 12, 0)
            planet1 = getattr(ephem, planet1_name)()
            planet2 = getattr(ephem, planet2_name)()
            
            planet1.compute(dt)
            planet2.compute(dt)
            
            lon1 = math.degrees(ephem.Ecliptic(planet1).lon)
            lon2 = math.degrees(ephem.Ecliptic(planet2).lon)
            
            angle_diff = abs(lon1 - lon2) % 360
            angle = min(angle_diff, 360 - angle_diff)
            
            aspect = None
            if angle <= orb:
                aspect = ('Conjunction ☌', 0)
            elif abs(angle - 180) <= orb:
                aspect = ('Opposition ☍', 180)
            elif abs(angle - 90) <= orb:
                aspect = ('Square ☐', 90)
            elif abs(angle - 120) <= orb:
                aspect = ('Trine △', 120)
                
            if aspect:
                aspects.append((dt.date(), aspect[0], aspect[1]))
                
        except Exception as e:
            print(f"Error calculating aspects: {e}")
            return []
        
        current_date += datetime.timedelta(days=1)
    
    return aspects

def find_planets_at_special_longitudes(year):
    special_longitudes = [0, 1, 24, 25, 48, 49, 72, 73, 96, 97, 
                         120, 121, 145, 146, 169, 170, 193, 194, 
                         217, 218, 241, 242, 265, 266, 289, 290, 
                         313, 314, 337, 338]
    
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    current_date = start_date
    
    results = []
    
    print(f"\nSearching for planets at special longitudes in {year}...")
    
    while current_date < end_date:
        for planet_name in planets:
            try:
                planet = getattr(ephem, planet_name)()
                planet.compute(current_date)
                lon = math.degrees(ephem.Ecliptic(planet).lon)
                normalized_lon = lon % 360
                
                for special_lon in special_longitudes:
                    if abs(normalized_lon - special_lon) < 0.5:
                        sign = get_astrological_sign(normalized_lon)
                        degree = normalized_lon % 30
                        
                        formatted_date = current_date.strftime('%Y-%m-%d %H:%M:%S UT')
                        
                        results.append({
                            'date': current_date.date(),  # Store date separately for grouping
                            'datetime': formatted_date,
                            'planet': planet_name,
                            'longitude': round(normalized_lon, 2),
                            'sign': sign,
                            'degree': round(degree, 2)
                        })
                        
            except AttributeError:
                continue
        
        current_date += datetime.timedelta(days=1)
    
    if results:
        print("\nPlanets at special longitudes found:")
        print("{:<20} {:<10} {:<8} {:<12} {:<6}".format(
            "Date/Time", "Planet", "Longitude", "Sign", "Degree"))
        print("=" * 60)
        
        current_display_date = None
        for result in sorted(results, key=lambda x: x['date']):
            if current_display_date != result['date']:
                if current_display_date is not None:
                    print("=" * 60)
                current_display_date = result['date']
                print(f"=== {current_display_date.strftime('%Y-%m-%d')} ===")
            
            print("{:<20} {:<10} {:<8} {:<12} {:<6}".format(
                result['datetime'],
                result['planet'],
                result['longitude'],
                result['sign'],
                result['degree']))
        
        print("=" * 60)
    else:
        print("No planets found at the specified longitudes during this year.")

def get_planet_aspects_for_month():
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    # Get user input
    print("\nAvailable planets:", ', '.join(planets))
    planet_name = input("Enter planet name: ").strip().capitalize()
    year = int(input("Enter year: "))
    month = int(input("Enter month (1-12): "))
    
    if planet_name not in planets:
        print("Invalid planet name. Please choose from the available planets.")
        return
    
    # Set date range
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)
    
    current_date = start_date
    results = []
    orb = 1.0  # 1 degree orb for aspect detection
    
    print(f"\nCalculating aspects for {planet_name} during {start_date.strftime('%B %Y')}...")
    
    while current_date < end_date:
        try:
            # Compute position of the main planet
            main_planet = getattr(ephem, planet_name)()
            main_planet.compute(current_date)
            main_lon = math.degrees(ephem.Ecliptic(main_planet).lon)
            
            # Check aspects with other planets
            for other_planet_name in planets:
                if other_planet_name == planet_name:
                    continue  # Skip self-comparison
                
                try:
                    other_planet = getattr(ephem, other_planet_name)()
                    other_planet.compute(current_date)
                    other_lon = math.degrees(ephem.Ecliptic(other_planet).lon)
                    
                    # Calculate angular difference
                    angle_diff = abs(main_lon - other_lon) % 360
                    angle = min(angle_diff, 360 - angle_diff)
                    
                    # Determine aspect
                    aspect = None
                    if angle <= orb:
                        aspect = ('Conjunction ☌', 0)
                    elif abs(angle - 180) <= orb:
                        aspect = ('Opposition ☍', 180)
                    elif abs(angle - 90) <= orb:
                        aspect = ('Square ☐', 90)
                    elif abs(angle - 120) <= orb:
                        aspect = ('Trine △', 120)
                    
                    if aspect:
                        results.append({
                            'date': current_date,
                            'planet1': planet_name,
                            'planet2': other_planet_name,
                            'aspect': aspect[0],
                            'angle': aspect[1],
                            'exact_angle': round(angle, 2)
                        })
                        
                except AttributeError:
                    continue  # Skip if planet doesn't exist in ephem
            
        except Exception as e:
            print(f"Error calculating aspects: {e}")
            continue
        
        # Move to next day (or smaller interval if you prefer)
        current_date += datetime.timedelta(days=1)
    
    # Display results
    if results:
        print(f"\nAspects for {planet_name} during {start_date.strftime('%B %Y')}:")
        print("{:<20} {:<15} {:<10} {:<15} {:<8}".format(
            "Date", "Planet 1", "Aspect", "Planet 2", "Angle"))
        print("=" * 80)
        
        current_display_date = None
        for result in sorted(results, key=lambda x: x['date']):
            if current_display_date != result['date'].date():
                if current_display_date is not None:
                    print("-" * 80)
                current_display_date = result['date'].date()
            
            print("{:<20} {:<15} {:<10} {:<15} {:<8}°".format(
                result['date'].strftime('%Y-%m-%d %H:%M UT'),
                result['planet1'],
                result['aspect'],
                result['planet2'],
                result['angle']))
        
        print("=" * 80)
    else:
        print(f"No aspects found for {planet_name} during this period.")

def menu():
    while True:
        print("\nMenu:")
        print("1. Calculate new moons and degrees for a given year")
        print("2. Get exact time and date for a specific year, month, sign, and degree")
        print("3. Find major aspects between two planets")
        print("4. Find planets at special longitudes")
        print("5. Find all aspects for a planet during a month")
        print("6. Exit")
        choice = int(input("Enter your choice: "))
        
        if choice == 1:
            year = int(input("Enter year to calculate new moons: "))
            print_new_moon_info(year)
            input_degree = int(input("Enter degree to find information for: "))
            get_info_for_user_degree(year, input_degree)
            
        elif choice == 2:
            get_exact_time_for_degree()
            
        elif choice == 3:
            planet1 = input("Enter first planet (e.g., Mars): ").strip().capitalize()
            planet2 = input("Enter second planet (e.g., Venus): ").strip().capitalize()
            year = int(input("Enter year: "))
            
            aspects = find_planetary_aspects(planet1, planet2, year)
            
            if aspects:
                print(f"\nMajor aspects between {planet1} and {planet2} in {year}:")
                for date, aspect, angle in aspects:
                    print(f"{date.strftime('%Y-%m-%d')}: {aspect} ({angle}°)")
            else:
                print(f"No major aspects found between {planet1} and {planet2} in {year}")
                
        elif choice == 4:
            year = int(input("Enter year to search for planets at special longitudes: "))
            find_planets_at_special_longitudes(year)
            
        elif choice == 5:
            get_planet_aspects_for_month()
            
        elif choice == 6:
            break
            
        else:
            print("Invalid choice. Please try again.")
# Run the menu
menu()
