# System
You are a helpful assistant. Given a list of people and power plant locations, find the specified person and determine the closest power plant to their location.
Return the person's name, surname, access level, and the code of the closest power plant.

# User
<people_json>
{people_json}
</people_json>

<power_plant_locations>
{locations_json}
</power_plant_locations>

Find a person that has location close to a powerplant. Return their details, access level with the closest power plant code.
1) Start by using websearch to find latitude and longitude of each power plant (corresponding citi coordinats are enough).
2) Iterate over each person:
    a) Use tool to get locations corresponding to person (with latitude and longitude).
    b) Use tool to calculate closest powerplant 
3) Find a smallest distance person - power plant pair
4) Fetch this person's access level
5) Return data with person's name, surname, access level, and the code of the closest power plant.
