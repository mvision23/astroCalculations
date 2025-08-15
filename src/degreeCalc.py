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
            elif abs(angle - 60) <= orb:
                aspect = ('Sextile ⚹', 60)
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
                    elif abs(angle - 60) <= orb:
                        aspect = ('Sextile ⚹', 60)
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

def find_repeating_aspects():
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    # Get user input
    print("\nAvailable planets:", ', '.join(planets))
    planet_name = input("Enter planet name: ").strip().capitalize()
    year = int(input("Enter year: "))
    
    if planet_name not in planets:
        print("Invalid planet name. Please choose from the available planets.")
        return
    
    # Set date range
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    current_date = start_date
    
    aspect_records = {}
    orb = 1.0  # 1 degree orb for aspect detection
    
    print(f"\nFinding repeating aspects for {planet_name} during {year}...")
    
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
                    elif abs(angle - 60) <= orb:
                       aspect = ('Sextile ⚹', 60)
                    elif abs(angle - 180) <= orb:
                        aspect = ('Opposition ☍', 180)
                    elif abs(angle - 90) <= orb:
                        aspect = ('Square ☐', 90)
                    elif abs(angle - 120) <= orb:
                        aspect = ('Trine △', 120)
                    
                    if aspect:
                        aspect_key = (other_planet_name, aspect[0])  # Now grouped by other planet
                        if aspect_key not in aspect_records:
                            aspect_records[aspect_key] = []
                        aspect_records[aspect_key].append(current_date)
                        
                except AttributeError:
                    continue  # Skip if planet doesn't exist in ephem
            
        except Exception as e:
            print(f"Error calculating aspects: {e}")
            continue
        
        # Move to next day
        current_date += datetime.timedelta(days=1)
    
    # Filter for aspects that occurred multiple times
    repeating_aspects = {k: v for k, v in aspect_records.items() if len(v) > 1}
    
    # Group by aspecting planet
    planet_aspects = {}
    for (other_planet, aspect), dates in repeating_aspects.items():
        if other_planet not in planet_aspects:
            planet_aspects[other_planet] = []
        planet_aspects[other_planet].append((aspect, dates))
    
    # Display results grouped by planet
    if planet_aspects:
        print(f"\nRepeating aspects for {planet_name} in {year} (grouped by aspecting planet):")
        print("=" * 80)
        for other_planet, aspects in planet_aspects.items():
            print(f"\nWith {other_planet}:")
            for aspect, dates in aspects:
                print(f"  {aspect} (occurred {len(dates)} times):")
                for i, date in enumerate(dates, 1):
                    print(f"    {i}. {date.strftime('%Y-%m-%d %H:%M UT')}")
        print("=" * 80)
    else:
        print(f"No repeating aspects found for {planet_name} in {year}")

def find_repeating_aspects_by_date():
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    # Get user input
    print("\nAvailable planets:", ', '.join(planets))
    planet_name = input("Enter planet name: ").strip().capitalize()
    year = int(input("Enter year: "))
    
    if planet_name not in planets:
        print("Invalid planet name. Please choose from the available planets.")
        return
    
    # Set date range
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    current_date = start_date
    
    aspect_records = {}
    orb = 1.0  # 1 degree orb for aspect detection
    
    print(f"\nFinding repeating aspects for {planet_name} during {year} grouped by date...")
    
    while current_date < end_date:
        try:
            # Compute position of the main planet
            main_planet = getattr(ephem, planet_name)()
            main_planet.compute(current_date)
            main_lon = math.degrees(ephem.Ecliptic(main_planet).lon)
            
            # Check aspects with other planets
            date_aspects = []
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
                    elif abs(angle - 60) <= orb:
                        aspect = ('Sextile ⚹', 60)
                    elif abs(angle - 180) <= orb:
                        aspect = ('Opposition ☍', 180)
                    elif abs(angle - 90) <= orb:
                        aspect = ('Square ☐', 90)
                    elif abs(angle - 120) <= orb:
                        aspect = ('Trine △', 120)
                    
                    if aspect:
                        date_aspects.append((other_planet_name, aspect[0], angle))
                        
                except AttributeError:
                    continue  # Skip if planet doesn't exist in ephem
            
            if date_aspects:
                date_key = current_date.date()
                if date_key not in aspect_records:
                    aspect_records[date_key] = []
                aspect_records[date_key].extend(date_aspects)
            
        except Exception as e:
            print(f"Error calculating aspects: {e}")
            continue
        
        # Move to next day
        current_date += datetime.timedelta(days=1)
    
    # Filter for dates with multiple aspects
    multi_aspect_dates = {k: v for k, v in aspect_records.items() if len(v) > 1}
    
    # Display results grouped by date
    if multi_aspect_dates:
        print(f"\nDates with multiple aspects for {planet_name} in {year}:")
        print("=" * 100)
        for date, aspects in sorted(multi_aspect_dates.items()):
            print(f"\nDate: {date.strftime('%Y-%m-%d')}")
            print("-" * 50)
            for planet, aspect, angle in aspects:
                print(f"  • {aspect} with {planet} ({angle}°)")
        print("=" * 100)
    else:
        print(f"No dates with multiple aspects found for {planet_name} in {year}")

def find_multiple_aspect_dates():
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    # Get user input
    print("\nAvailable planets:", ', '.join(planets))
    planet_name = input("Enter planet name: ").strip().capitalize()
    year = int(input("Enter year: "))
    
    if planet_name not in planets:
        print("Invalid planet name. Please choose from the available planets.")
        return
    
    # Set date range
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    current_date = start_date
    
    date_aspects = {}
    orb = 1.0  # 1 degree orb for aspect detection
    
    print(f"\nFinding dates with 2+ aspects for {planet_name} in {year}...")
    
    while current_date < end_date:
        try:
            # Compute position of the main planet
            main_planet = getattr(ephem, planet_name)()
            main_planet.compute(current_date)
            main_lon = math.degrees(ephem.Ecliptic(main_planet).lon)
            
            aspects_on_date = []
            
            # Check aspects with other planets
            for other_planet_name in planets:
                if other_planet_name == planet_name:
                    continue
                
                try:
                    other_planet = getattr(ephem, other_planet_name)()
                    other_planet.compute(current_date)
                    other_lon = math.degrees(ephem.Ecliptic(other_planet).lon)
                    
                    # Calculate angular difference
                    angle_diff = abs(main_lon - other_lon) % 360
                    angle = min(angle_diff, 360 - angle_diff)
                    
                    # Determine aspect
                    if angle <= orb:
                        aspects_on_date.append((other_planet_name, 'Conjunction ☌', 0))
                    elif abs(angle - 60) <= orb:
                        aspects_on_date.append((other_planet_name, 'Sextile ⚹', 60))
                    elif abs(angle - 180) <= orb:
                        aspects_on_date.append((other_planet_name, 'Opposition ☍', 180))
                    elif abs(angle - 90) <= orb:
                        aspects_on_date.append((other_planet_name, 'Square ☐', 90))
                    elif abs(angle - 120) <= orb:
                        aspects_on_date.append((other_planet_name, 'Trine △', 120))
                        
                except AttributeError:
                    continue
            
            # Only store dates with 2+ aspects
            if len(aspects_on_date) >= 2:
                date_key = current_date.date()
                date_aspects[date_key] = aspects_on_date
                
        except Exception as e:
            print(f"Error calculating aspects: {e}")
            continue
        
        # Move to next day
        current_date += datetime.timedelta(days=1)
    
    # Display results
    if date_aspects:
        print(f"\nDates with 2+ aspects for {planet_name} in {year}:")
        print("=" * 80)
        for date, aspects in sorted(date_aspects.items()):
            print(f"\n{date.strftime('%Y-%m-%d')}:")
            for planet, aspect, angle in aspects:
                print(f"  • {aspect} with {planet} ({angle}°)")
        print("=" * 80)
    else:
        print(f"No dates found with 2+ aspects for {planet_name} in {year}")

def calculate_planetary_positions():
    planets = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
        'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
    ]
    
    # Get user input
    date_str = input("Enter date (YYYY-MM-DD): ").strip()
    try:
        input_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return
    
    print(f"\nPlanetary positions for {input_date.strftime('%Y-%m-%d')}:")
    print("=" * 100)
    print("{:<10} {:<10} {:<15} {:<15} {:<10}".format(
        "Planet", "Longitude", "Sign", "Degree", "Retrograde"))
    print("-" * 100)
    
    # We'll track previous positions to detect retrograde
    prev_positions = {}
    
    # First compute all positions for the day before to compare
    prev_date = input_date - datetime.timedelta(days=1)
    for planet_name in planets:
        try:
            planet = getattr(ephem, planet_name)()
            planet.compute(prev_date)
            ecliptic = ephem.Ecliptic(planet)
            prev_positions[planet_name] = math.degrees(ecliptic.lon)
        except:
            prev_positions[planet_name] = None
    
    # Now compute current positions
    for planet_name in planets:
        try:
            # Calculate position
            planet = getattr(ephem, planet_name)()
            planet.compute(input_date)
            ecliptic = ephem.Ecliptic(planet)
            lon_degrees = math.degrees(ecliptic.lon)
            normalized_lon = lon_degrees % 360
            sign = get_astrological_sign(normalized_lon)
            degree = normalized_lon % 30
            
            # Check retrograde status by comparing with previous day
            retrograde = ""
            if planet_name not in ['Sun', 'Moon'] and prev_positions[planet_name] is not None:
                # Calculate daily motion
                current_lon = normalized_lon
                prev_lon = prev_positions[planet_name] % 360
                motion = (current_lon - prev_lon) % 360
                # If motion is > 180 degrees, it's actually moving backward
                if motion > 180:
                    retrograde = "Rx"
            
            # Format output
            print("{:<10} {:<10.2f}° {:<15} {:<15.2f}° {:<10}".format(
                planet_name,
                normalized_lon,
                sign,
                degree,
                retrograde))
                
        except Exception as e:
            print(f"Error calculating {planet_name}: {str(e)}")
            continue
    
    print("=" * 100)

def find_planets_at_zero_degree():
    planets = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
        'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
    ]
    
    year = int(input("Enter year to analyze: "))
    orb = 0.5  # Orb of 0.5 degrees for precision
    
    print(f"\nFinding planets at 0° of signs in {year} (grouped by month):")
    print("=" * 100)
    print("{:<12} {:<10} {:<15} {:<10} {:<10}".format(
        "Date", "Planet", "Sign", "Degree", "Retrograde"))
    print("-" * 100)
    
    # Initialize monthly results dictionary
    monthly_results = {month: {} for month in range(1, 13)}
    
    current_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    
    while current_date < end_date:
        for planet_name in planets:
            try:
                planet = getattr(ephem, planet_name)()
                planet.compute(current_date)
                lon = math.degrees(ephem.Ecliptic(planet).lon)
                normalized_lon = lon % 360
                degree = normalized_lon % 30
                
                # Check retrograde status (except for Sun and Moon)
                retrograde = ""
                if planet_name not in ['Sun', 'Moon']:
                    # Compare with position 6 hours ago to determine motion
                    prev_date = current_date - datetime.timedelta(hours=6)
                    planet_prev = getattr(ephem, planet_name)()
                    planet_prev.compute(prev_date)
                    lon_prev = math.degrees(ephem.Ecliptic(planet_prev).lon)
                    motion = (normalized_lon - lon_prev) % 360
                    if motion > 180:
                        retrograde = "Rx"
                
                # Check if planet is within orb of 0° of any sign
                if degree <= orb or degree >= (30 - orb):
                    sign = get_astrological_sign(normalized_lon)
                    date_key = current_date.date()
                    
                    # Only count when entering a new sign (approaching 0°)
                    if degree <= orb:
                        month = current_date.month
                        if planet_name not in monthly_results[month].get(date_key, {}):
                            if date_key not in monthly_results[month]:
                                monthly_results[month][date_key] = {}
                            monthly_results[month][date_key][planet_name] = (
                                sign,
                                round(degree, 2),
                                retrograde
                            )
                        
            except Exception as e:
                print(f"Error calculating {planet_name}: {str(e)}")
                continue
        
        # Move forward by 6 hours for more precise timing
        current_date += datetime.timedelta(hours=6)
    
    # Print results grouped by month
    found_any = False
    for month in range(1, 13):
        month_name = datetime.date(year, month, 1).strftime('%B')
        month_data = monthly_results[month]
        
        if month_data:
            found_any = True
            print(f"\n{month_name}:")
            print("-" * 100)
            
            # Sort events by date
            for date in sorted(month_data.keys()):
                for planet, (sign, degree, retrograde) in month_data[date].items():
                    print("{:<12} {:<10} {:<15} {:<10.2f}° {:<10}".format(
                        date.strftime('%Y-%m-%d'),
                        planet,
                        sign,
                        degree,
                        retrograde))
    
    if not found_any:
        print("No planets found at 0° of signs during this year.")
    print("=" * 100)

def find_planetary_alignments():
    planets = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
        'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
    ]
    
    year = int(input("Enter year to analyze: "))
    orb = 1.0  # 1 degree orb for alignment detection
    
    print(f"\nFinding planetary alignments in {year} (same 24° segment):")
    print("=" * 80)
    
    current_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    
    daily_results = {}
    
    while current_date < end_date:
        planet_positions = {}
        segment_groups = {}
        
        for planet_name in planets:
            try:
                planet = getattr(ephem, planet_name)()
                planet.compute(current_date)
                lon = math.degrees(ephem.Ecliptic(planet).lon)
                normalized_lon = lon % 360
                if normalized_lon == 0:
                    normalized_lon = 360
                
                # Determine segment (1-24) and circle (0-14)
                segment = int(normalized_lon % 24) or 24  # 1-24
                circle = int((normalized_lon - 1) // 24)   # 0-14
                
                # Determine retrograde status
                retrograde = False
                if planet_name not in ['Sun', 'Moon']:
                    prev_date = current_date - datetime.timedelta(hours=6)
                    planet_prev = getattr(ephem, planet_name)()
                    planet_prev.compute(prev_date)
                    lon_prev = math.degrees(ephem.Ecliptic(planet_prev).lon)
                    motion = (normalized_lon - lon_prev) % 360
                    if motion > 180:
                        retrograde = True
                
                planet_data = {
                    'degree': normalized_lon,
                    'retrograde': retrograde
                }
                
                # Group by segment
                if segment not in segment_groups:
                    segment_groups[segment] = []
                segment_groups[segment].append((planet_name, planet_data))
                
            except Exception as e:
                print(f"Error calculating {planet_name}: {str(e)}")
                continue
        
        # Find alignments (same segment)
        date_key = current_date.date()
        for segment, planets_in_segment in segment_groups.items():
            if len(planets_in_segment) >= 2:
                if date_key not in daily_results:
                    daily_results[date_key] = []
                
                # Format planet names with Rx if retrograde
                planet_list = []
                degrees = []
                for planet_name, data in planets_in_segment:
                    display_name = planet_name
                    if data['retrograde']:
                        display_name += "(Rx)"
                    planet_list.append(display_name)
                    degrees.append(f"{data['degree']:.1f}°")
                
                daily_results[date_key].append((
                    segment,
                    ", ".join(planet_list),
                    ", ".join(degrees)
                ))
        
        current_date += datetime.timedelta(days=1)
    
    # Print results
    if daily_results:
        for date in sorted(daily_results.keys()):
            print(f"===========================================================")
            print(f"==={date.strftime('%Y-%m-%d')}===")
            for segment, planet_list, degree_list in daily_results[date]:
                # Apply color formatting based on segment
                if segment == 1:
                    # Green for segment 1
                    planet_list = f"\033[92m{planet_list.ljust(30)}\033[0m"
                    degree_list = f"\033[92m{degree_list}\033[0m"
                elif segment == 24:
                    # Red for segment 24
                    planet_list = f"\033[91m{planet_list.ljust(30)}\033[0m"
                    degree_list = f"\033[91m{degree_list}\033[0m"
                
                print(f" {planet_list.ljust(30)} {degree_list}")
    else:
        print("No planetary alignments found during this year.")
    print("=" * 80)

def calculate_monthly_aspects():
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    # Get user input
    year = int(input("Enter year: "))
    month = int(input("Enter month (1-12): "))
    orb = 1.0  # 1 degree orb for aspect detection
    
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)
    
    print(f"\nCalculating all planetary aspects for {start_date.strftime('%B %Y')}:")
    print("=" * 120)
    print("{:<12} {:<25} {:<15} {:<25} {:<10}".format(
        "Date", "Planet 1 (Sign°)", "Aspect", "Planet 2 (Sign°)", "Angle"))
    print("-" * 120)
    
    aspect_counts = {}
    current_date = start_date
    
    while current_date < end_date:
        # Calculate positions and signs for all planets
        planet_data = {}
        for planet_name in planets:
            try:
                planet = getattr(ephem, planet_name)()
                planet.compute(current_date)
                lon = math.degrees(ephem.Ecliptic(planet).lon)
                sign = get_astrological_sign(lon)
                degree = lon % 30
                planet_data[planet_name] = {
                    'lon': lon,
                    'sign': sign,
                    'degree': degree
                }
            except Exception as e:
                print(f"Error calculating {planet_name}: {str(e)}")
                continue
        
        # Check all planet pairs
        checked_pairs = set()
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                planet1 = planets[i]
                planet2 = planets[j]
                
                if planet1 not in planet_data or planet2 not in planet_data:
                    continue
                
                data1 = planet_data[planet1]
                data2 = planet_data[planet2]
                angle_diff = abs(data1['lon'] - data2['lon']) % 360
                angle = min(angle_diff, 360 - angle_diff)
                
                # Determine aspect
                aspect = None
                if angle <= orb:
                    aspect = ('Conjunction ☌', 0)
                elif abs(angle - 60) <= orb:
                    aspect = ('Sextile ⚹', 60)
                elif abs(angle - 90) <= orb:
                    aspect = ('Square ☐', 90)
                elif abs(angle - 120) <= orb:
                    aspect = ('Trine △', 120)
                elif abs(angle - 180) <= orb:
                    aspect = ('Opposition ☍', 180)
                
                if aspect:
                    date_key = current_date.date()
                    aspect_key = (planet1, aspect[0], planet2)
                    
                    # Count aspect occurrences
                    if aspect_key not in aspect_counts:
                        aspect_counts[aspect_key] = 0
                    aspect_counts[aspect_key] += 1
                    
                    # Format planet info with sign and degree
                    planet1_info = f"{planet1} ({data1['sign']} {data1['degree']:.1f}°)"
                    planet2_info = f"{planet2} ({data2['sign']} {data2['degree']:.1f}°)"
                    
                    # Print daily aspects
                    print("{:<12} {:<25} {:<15} {:<25} {:<10}°".format(
                        date_key.strftime('%Y-%m-%d'),
                        planet1_info,
                        aspect[0],
                        planet2_info,
                        aspect[1]))
        
        current_date += datetime.timedelta(days=1)
    
    # Print aspect summary
    if aspect_counts:
        print("\nAspect Summary for the month:")
        print("-" * 70)
        for (planet1, aspect, planet2), count in aspect_counts.items():
            print(f"{aspect} between {planet1} and {planet2}: {count} times")
    else:
        print("\nNo planetary aspects found during this month.")
    print("=" * 120)

def menu():
    while True:
        print("\nMenu:")
        print("1. Calculate new moons and degrees for a given year")
        print("2. Get exact time and date for a specific year, month, sign, and degree")
        print("3. Find major aspects between two planets")
        print("4. Find planets at special longitudes")
        print("5. Find all aspects for a planet during a month")
        print("6. Find repeating aspects for a planet during a year")
        print("7. Find repeating aspects for a planet during a year (grouped by date)")
        print("8. Find dates with 2+ aspects for a planet")
        #print("9. Find repeating aspects for a planet during a year (grouped by planet)")
        print("9. Calculate all planetary positions for a date")
        print("10. Find planets at 0° of signs (by month)")
        print("11. Find planetary alignments (same degree/segment)")
        print("12. Calculate all aspects for all planets in a month")
        print("13. Exit")
        #print("12. Exit")
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
            find_repeating_aspects()
            
        elif choice == 7:
            find_repeating_aspects_by_date()
            
        elif choice == 8:
            find_multiple_aspect_dates()
        
        elif choice == 9:
            calculate_planetary_positions()
                
        elif choice == 10:
            find_planets_at_zero_degree()

        elif choice == 11:
            find_planetary_alignments()
        
        elif choice == 12:
            calculate_monthly_aspects()
            
        elif choice == 12:
            break
        else:
            print("Invalid choice. Please try again.")
# Run the menu
menu()
