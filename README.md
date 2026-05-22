# SwapLah - Student Co-op Marketplace

SwapLah is a web-based marketplace built for polytechnic students to securely buy, sell, and swap pre-owned items like textbooks, lab equipment, and electronics within a trusted campus community.

## Local Development Setup

To contribute to this project, you will need to set up a local Python Virtual Environment (venv). This ensures that all developers are using the exact same library versions and prevents conflicts with your system's global Python packages.

### Prerequisites

Ensure you have Python 3.8 or higher installed on your machine. You can check your version by running the following in your terminal: python --version

### Step 1: Clone the Repository

Clone the GitLab repository to your local machine and navigate into the project directory

git clone cd swaplah

### Step 2: Create the Virtual Environment

Create a new virtual environment named ".venv" inside the project folder. Run the following command in your terminal:

For Windows, macOS, and Linux:

python -m venv .venv 

(Note: If "python" doesn't work on macOS/Linux, try using "python3 -m venv .venv")

### Step 3: Activate the Virtual Environment

You must activate the virtual environment every time you open a new terminal to work on this project.

For Windows (Command Prompt):

.venv\\Scripts\\activate.bat

For Windows (PowerShell):

 .venv\\Scripts\\Activate.ps1

For macOS and Linux:

source .venv/bin/activate

Success Check: You will know it is activated when you see "(.venv)" appear at the very beginning of your terminal prompt line.

### Step 4: Install Dependencies

With the virtual environment activated, install all the required Python packages listed in the requirements file

pip install -r requirements.txt

### Step 5: Environment Variables

This project requires secret keys and database configurations that should never be pushed to version control.

1.  Duplicate the ".env.example" file.
2.  Rename the duplicated file to ".env".
3.  Fill in your local configuration values inside the ".env" file. (Note: Ensure your ".env" file remains listed in your ".gitignore" file so it is never uploaded to GitLab).

### Step 6: Run the Application

Start the local Flask development server

flask run

(Or run it directly using Python, depending on your setup)

python run.py

## Deactivating the Environment

When you are done working and want to return to your normal system terminal, you can safely exit the virtual environment by running

deactivate