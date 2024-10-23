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
year = int(input("Enter year to calculate new moons: "))
print_new_moon_info(year)

input_degree = int(input("Enter degree to find information for: "))
get_info_for_user_degree(year, input_degree)
