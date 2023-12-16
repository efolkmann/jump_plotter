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

- Install python
- Install dependencies

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/4d30/jump-plotter.git
   ```
2. Install dependencies
   ```sh
   python -m venv venv
   .\venv\Scripts\activate (Windows)
   source venv/bin/activate (Linux/Mac)
   pip install -r Pipfile.lock
   ```

## Usage

Edit plot.conf. Set *rto* to the path of RTO/ on your system.
```sh
nano plot.conf
```
Run
```sh
python main.py
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request

