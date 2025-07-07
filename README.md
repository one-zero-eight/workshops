<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/InNoHassle-Workshops-Check-In/backend">
    <img src="https://avatars.githubusercontent.com/u/215998499?s=48&v=4" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">InNoHassle Workshops Backend</h3>

  <p align="center">
    Backend for the InNoHassle ecosystem, managing workshops, users, and check-ins.<br />
    <a href="https://github.com/InNoHassle-Workshops-Check-In/backend"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://workshops.innohassle.ru">View Demo</a>
    &middot;
    <a href="https://github.com/InNoHassle-Workshops-Check-In/backend/issues">Issues</a>
    &middot;
    <a href="https://github.com/InNoHassle-Workshops-Check-In/backend/pulls">Pull Requests</a>
  </p>
</div>

<!-- ARCHITECTURE DIAGRAM (OPTIONAL) -->
<br />
<div align="center">
  <img src="docs/architecture/static-view/AppArch.png" alt="Architecture Diagram" width="400"/>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#built-with">Built With</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
    <li><a href="#contributors">Contributors</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

**Workshops API** is the backend for the InNoHassle ecosystem. It provides:
- User management (roles, registration, authentication via JWT)
- Workshop CRUD (create, read, update, delete)
- Workshop check-in and capacity management
- Integration with InNoHassle Accounts
- Admin/user role separation
- Async database access (SQLModel, SQLAlchemy, asyncpg)
- API documentation via OpenAPI/Swagger

This backend is built with FastAPI and PostgreSQL, designed for scalability and easy integration with the InNoHassle platform.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

This section should list any major frameworks/libraries used to bootstrap your project. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.

* [FastAPI](https://fastapi.tiangolo.com/)
* [SQLModel](https://sqlmodel.tiangolo.com/) & [SQLAlchemy](https://www.sqlalchemy.org/)
* [PostgreSQL](https://www.postgresql.org/)
* [Alembic](https://alembic.sqlalchemy.org/) (migrations)
* [Authlib](https://docs.authlib.org/), [python-jose](https://python-jose.readthedocs.io/) (JWT)
* [aiosqlite](https://github.com/omnilib/aiosqlite), [asyncpg](https://github.com/MagicStack/asyncpg)
* [python-dotenv](https://github.com/theskumar/python-dotenv), [pydantic](https://docs.pydantic.dev/)
* [Uvicorn](https://www.uvicorn.org/) (ASGI server)
* [Pytest](https://docs.pytest.org/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* Python 3.13+
* PostgreSQL 15+

### Installation

_Below is an example of how you can instruct your audience on installing and setting up your app. This template doesn't rely on any external dependencies or services._

1. Clone the repo
   ```sh
   git clone https://github.com/InNoHassle-Workshops-Check-In/backend.git
   cd backend
   ```
2. Install [uv](https://astral.sh/uv/) (fast Python package manager)
   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. Create and activate a virtual environment
   ```sh
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install dependencies
   ```sh
   uv pip install -e .
   ```
5. Create a `.env` file (see `.example.env` for details)
6. Create a `logs` directory in the project root
7. Run the backend
   ```sh
   uv run src/api/__main__.py
   ```

### Configuration
Set the following in your `.env` file:
- `DATABASE_URI` (e.g., `postgresql+asyncpg://user:password@localhost:5432/dbname`)
- `API_JWT_TOKEN` (JWT token for InNoHassle Accounts integration)
- `IS_PROD` (set to `Prod` for production, otherwise for development)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] User and workshop models
- [x] JWT authentication
- [x] Workshop check-in logic
- [x] Admin/user role separation
- [x] Alembic migrations
- [ ] Multi-language support
- [ ] Additional templates and documentation
- [ ] More granular permissions

See the [open issues](https://github.com/InNoHassle-Workshops-Check-In/backend/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact
Maintainer: [one-zero-eight (Telegram)](https://t.me/one_zero_eight)

Project Link: [https://github.com/InNoHassle-Workshops-Check-In/backend](https://github.com/InNoHassle-Workshops-Check-In/backend)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Use this space to list resources you find helpful and would like to give credit to. I've included a few of my favorites to kick things off!

* [FastAPI](https://fastapi.tiangolo.com/)
* [SQLModel](https://sqlmodel.tiangolo.com/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Authlib](https://docs.authlib.org/)
* [python-jose](https://python-jose.readthedocs.io/)
* [Uvicorn](https://www.uvicorn.org/)
* [Pytest](https://docs.pytest.org/)
* [Choose an Open Source License](https://choosealicense.com)
* [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet)
* [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
* [Malven's Grid Cheatsheet](https://grid.malven.co/)
* [Img Shields](https://shields.io)
* [GitHub Pages](https://pages.github.com)
* [Font Awesome](https://fontawesome.com)
* [React Icons](https://react-icons.github.io/react-icons/search)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTORS -->
## Contributors

<a href="https://github.com/InNoHassle-Workshops-Check-In/backend/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=InNoHassle-Workshops-Check-In/backend" alt="Contributors" />
</a>

**Project contributors:**

- [@tomatoCoderq](https://github.com/tomatoCoderq)
- [@jakefish18](https://github.com/jakefish18)
- [@Kaghorz](https://github.com/Kaghorz)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/InNoHassle-Workshops-Check-In/backend.svg?style=for-the-badge
[contributors-url]: https://github.com/InNoHassle-Workshops-Check-In/backend/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/InNoHassle-Workshops-Check-In/backend.svg?style=for-the-badge
[forks-url]: https://github.com/InNoHassle-Workshops-Check-In/backend/network/members
[stars-shield]: https://img.shields.io/github/stars/InNoHassle-Workshops-Check-In/backend.svg?style=for-the-badge
[stars-url]: https://github.com/InNoHassle-Workshops-Check-In/backend/stargazers
[issues-shield]: https://img.shields.io/github/issues/InNoHassle-Workshops-Check-In/backend.svg?style=for-the-badge
[issues-url]: https://github.com/InNoHassle-Workshops-Check-In/backend/issues
[license-shield]: https://img.shields.io/github/license/InNoHassle-Workshops-Check-In/backend.svg?style=for-the-badge
[license-url]: https://github.com/InNoHassle-Workshops-Check-In/backend/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/one-zero-eight
