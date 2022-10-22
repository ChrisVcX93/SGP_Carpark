# SGP_Carpark Web App
- This app allows users to quickly find car parks nearby based on current user location anywhere in Singapore
![Screenshot 2022-10-22 at 12 26 10 PM](https://user-images.githubusercontent.com/63183714/197319040-97a1e642-1509-4c28-8cb1-c8507ff7d5fb.png)
- User is able to selet range of car parks from 500m to 2km
- Real time data is obtained from data.gov api 
- Pyspark is then used to engineer the data based on the current location and nearest distance 
- Onemap API is utilized to convert lat/lon coordinates to S3414(SVY21) format
![Screenshot 2022-10-22 at 12 41 11 PM](https://user-images.githubusercontent.com/63183714/197320127-16fdfd7c-4f63-484d-b179-3ab542ae5a7b.png)
- User is quickly able to determine if the carpark is available based on the color code
- red being 0 slots , yellow being <10 slots and green >= 20 slots 
![Screenshot 2022-10-22 at 12 33 27 PM](https://user-images.githubusercontent.com/63183714/197320160-88b5c616-b853-4301-89e9-b70752d912a7.png)
Geo maps are generated using Dash Leaflet , an open-source Javascript library 
![Screenshot 2022-10-22 at 12 53 40 PM](https://user-images.githubusercontent.com/63183714/197320542-4de4aa0d-82f8-42fc-a0e2-06e8fc4ac21c.png)
