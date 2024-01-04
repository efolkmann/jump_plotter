# Jump Plotter

A user application which displays data and solicits annotations from the user

## Table of Contents

- [Jump Plotter](#jump-plotter)
  - [Table of Contents](#table-of-contents)
  - [About the Project](#about-the-project)
    - [Built With](#built-with)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

## About the Project

A user-application to faciltate data annotations

### Built With

- [Python](https://www.python.org/)
- [Matplotlib](https://matplotlib.org/)

## Getting Started

To get started with this project, follow these steps:

### Prerequisites

- Install python-3.11
- Install dependencies

### Installation

1. Clone the repository
   ```sh
   git clone git@github.com:4d30/jump_plotter.git
   ```
2. Install Python

- Python 3.11.0+ is required
- [https://www.python.org/downloads/](https://www.python.org/downloads/)

3. Install dependencies
   ```sh
   python -m venv venv
   .\venv\Scripts\activate (Windows)
   source venv/bin/activate (Linux/Mac)
   pip install -r requirements.txt
   ```

## Usage

Edit plot.conf. Set *rto* to the path of RTO/ on your system.
```sh
nano plot.conf
```
Run
```sh
PYTHONUNBUFFERED=1; python main.py
```

## Notes

When to label a sensor as k (kill the whole sensor file):

1. Check if there is a sensor event before the jump that confirms or denies synchronization
Check if there is a sensor event after the jump that confirms or denies synchronization
IF yes to both, label the jump based on the results (a,b, or c)

2. Check for an obvious sensor discontinuity within the jump page (black). If so, label it as a.

IF you can't tell after checking 1 & 2, look at the jump duration

if jump is < 0.5 seconds, make a guess (bc the consequences of being wrong are small)
if jump is > 0.5 seconds, mark it k (bc the consequences of being wrong are large)

If you have to label a too many jumps with a guess (arbitrarily defined as 4 jumps), mark the sensor file as k



## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request

