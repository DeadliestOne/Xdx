import requests
import re

def extract_upi_info(upi_id):
    # Validate UPI ID format
    upi_pattern = r'^[a-zA-Z0-9.-]{2,256}@[a-zA-Z][a-zA-Z]{2,64}$'
    if not re.match(upi_pattern, upi_id):
        return "Invalid UPI ID format"

    # Extract handle from UPI ID
    handle = upi_id.split('@')[1]

    # API endpoint for UPI verification
    url = f"https://ifsc.razorpay.com/upi/{handle}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "UPI ID": upi_id,
                "Bank Name": data.get("BANK", "N/A"),
                "IFSC Code": data.get("IFSC", "N/A"),
                "Address": data.get("ADDRESS", "N/A"),
                "City": data.get("CITY", "N/A"),
                "State": data.get("STATE", "N/A"),
                "PSP": data.get("psp", "N/A")
            }
        else:
            return "Unable to fetch information for the given UPI ID"
    except requests.exceptions.RequestException:
        return "Error occurred while fetching information"

# Example usage
upi_id = "Anirb@axl"
result = extract_upi_info(upi_id)
print(result)
