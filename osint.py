import requests
import json
import re

def get_google_id(email):
    url = "https://people-pa.clients6.google.com/$rpc/google.internal.people.v2.minimal.PeopleApiAutocompleteMinimalService/ListAutocompletions"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = json.dumps([email, None, None, ["GMAIL_COMPOSE_WEB_POPULOUS"], 8, None, None, None, ["GMAIL_COMPOSE_WEB_POPULOUS", None, 2]])

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        match = re.search(r'"([0-9]{21})"', response.text)
        if match:
            return match.group(1)
    return None

def get_profile_info(google_id):
    url = f"https://www.google.com/maps/contrib/{google_id}"
    response = requests.get(url)
    if response.status_code == 200:
        name_match = re.search(r'<meta content="Contributions by (.*?)"', response.text)
        image_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text)
        
        name = name_match.group(1) if name_match else "Not found"
        image_url = image_match.group(1) if image_match else "Not found"
        
        return {"name": name, "profile_image": image_url}
    return None

def gmail_osint(email):
    print(f"Performing OSINT on: {email}")
    
    google_id = get_google_id(email)
    if not google_id:
        print("Could not retrieve Google ID.")
        return
    
    print(f"Google ID: {google_id}")
    
    profile_info = get_profile_info(google_id)
    if profile_info:
        print(f"Name: {profile_info['name']}")
        print(f"Profile Image URL: {profile_info['profile_image']}")
    else:
        print("Could not retrieve profile information.")

if __name__ == "__main__":
    email = input("Enter Gmail address: ")
    gmail_osint(email)
