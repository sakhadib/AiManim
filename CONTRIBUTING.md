# Contributing to AIManim

First off, thank you for considering contributing to AIManim! It's an open-source project, and community contributions are what make tools like this robust and feature-rich.

Whether you're fixing bugs, adding new AI providers, or building out the roadmap features, your help is incredibly valuable.

## 🗺️ Current Roadmap & Where We Need Help

We are actively looking for pull requests for the following major features:

1. **SymPy Integration:** Enabling actual data generation and accurate mathematical graphing.
2. **LaTeX Support:** Safely integrating LaTeX rendering for complex equations without breaking the easy Windows setup.
3. **Video Quality Improvements:** Tuning the Manim defaults for higher-quality renders and smoother animations.
4. **New AI Providers:** Expanding the backend (using the existing Strategy/Factory patterns).

## 🛠️ Development Setup

To get started, you'll need Python 3.10+, [Manim Community](https://www.manim.community/), and [FFmpeg](https://ffmpeg.org/) installed on your system.

1. **Fork and Clone:**
   Fork the repository to your own GitHub account and clone it locally.
   ```powershell
   git clone [https://github.com/YOUR_USERNAME/aimanim.git](https://github.com/YOUR_USERNAME/aimanim.git)
   cd aimanim
   ```

2. **Set up a Virtual Environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Development Dependencies:**
   Install the package in editable mode along with testing tools.
   ```powershell
   python -m pip install -e ".[dev]"
   ```

## 🏗️ Architecture Quick-Look

To help you navigate the codebase:
* **LLM Orchestration:** We use LangGraph to manage the context between the Scene Planner, the Code Generator, and the Reviewer (Self-Healing) agents. 
* **Provider Abstraction:** AI providers (OpenRouter, OpenAI, Gemini) are implemented using Strategy and Factory design patterns. If you want to add a new provider, simply inherit from the base provider class and implement the required methods. 
* **Error Handling:** The system catches Manim tracebacks and feeds them back to the LLM for automatic repair. When working on the codegen modules, ensure error logs remain clean and pass correctly to the repair loop.

## ✅ Pull Request Process

1. Create a new branch for your feature or bugfix (`git checkout -b feature/sympy-graphs`).
2. Write clean, documented code. If you are adding a new CLI parameter, be sure to update the table in `README.md`.
3. **Run Tests:** Ensure nothing is broken before submitting.
   ```powershell
   python -m pytest
   ```
4. **Syntax Check:**
   ```powershell
   python -m compileall math2manim tests
   ```
5. Push to your fork and submit a Pull Request to the `main` branch of the original repository. 

Please provide a clear description of what your PR does, the problem it solves, and any new dependencies it introduces.

## 📄 License
By contributing to AIManim, you agree that your contributions will be licensed under its MIT License.
