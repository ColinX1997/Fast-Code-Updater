# Fast-Code-Updater
# Background

When the code is not available for you, and the components/apps are writen by Python, and it's shared on one FTP server, this script could help you get the latest version of code and do local version control automatically

# Steps

Self-developed fttp code updater tool
Create a folder and put the component-version config file inside of it

Then modify the component and version you need:

![image](https://github.com/user-attachments/assets/725fb3b1-40a1-4cf8-b410-5ce259c2f0cd)

run init script (modify the path in this script to your own firstly)
![image](https://github.com/user-attachments/assets/f7227648-bac9-4062-890b-894dc265e4bf)
This script will then download all the component with specified version which defined in the txt file, like:
![image](https://github.com/user-attachments/assets/2ba8117b-335d-445d-8f41-44fbb5967e65)

run updater script when you know there are updates in component
also, you need to modify the script with your own path, like step2
and then just run it, it would help you download the latest version and unzip them to overwrite exist folder, and do git version control for them automatically:
![image](https://github.com/user-attachments/assets/e2f4ea73-bab8-4ffe-af82-d877a9309909)
