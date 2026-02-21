# LabMate AI
**Your Intelligent Laboratory and Research Collaboration Partner**

LabMate AI is a comprehensive experiment management and collaboration tool tailored for researchers, students, and educators. It combines strict data structuring with flexible AI assistance to help you track experiment progress, manage variables, and gain instant insights into experiment design.

---

## Core Features

### 1. Experiment Data Management
* **Version Control**: Automatically logs versions for every data update, ensuring complete traceability.
* **Structured Storage**: Safely stores names, descriptions, creators, and data in an SQLite database.
* **History Tracking**: Framework in place to review and restore historical data versions.

### 2. Experiment Plan Collaboration
* **Plan Formulation**: Define research goals, and establish lists for experimental steps and necessary materials.
* **Multi-user Collaboration**: Supports adding and removing collaborators to foster teamwork.
* **Dynamic Adjustment**: Readily modify steps and materials to flexibly respond to experimental changes.

### 3. AI Research Assistant
* **Flow Design**: Input a research goal (e.g., "Research plant photosynthesis") and the AI will auto-generate a recommended procedure.
* **Problem Decomposition**: Break down complex research questions into actionable sub-problems.
* **Standard Operating Procedures (SOP)**: Generate standard operation steps and safety precautions for your experiments.

### 4. Instrument Guide
* **Smart Query**: Quickly look up manuals and documents using keywords.
* **Extensibility**: Supports custom instrument databases strictly defined via JSON formatting.

---

## Getting Started

### System Requirements
* Python 3.6 or higher
* Streamlit (for UI graphical interface)
* Built-in SQLite3 support (included in Python standard library)

### Installation Steps

1. **Download the Project**
   Clone or download the archive to your local machine.

2. **Environment Setup**
   The core project utilizes Python standard libraries. To run the graphical interface, install Streamlit:
   ```bash
   pip install streamlit
   ```

### Execution Instructions

**Option 1: Graphical User Interface (Recommended)**
Run the application using Streamlit to access the modern web interface.
```bash
streamlit run app.py
```
This will open a local web server (usually at `http://localhost:8501`) where you can interact seamlessly via your default web browser.

**Option 2: Terminal Interface Demo**
To run the automated console demonstration:
```bash
python "LabMate AI.py" demo
```
To run the interactive terminal interface:
```bash
python "LabMate AI.py"
```

---

## Usage Guide (Via Web UI)

### 1. Identify Yourself
When you launch the Streamlit application, enter your name or user ID in the dedicated field on the left sidebar. All actions logged will be attributed to this identity.

### 2. Manage Experiments
Navigate to the "Experiment Management" tab. You can seamlessly view registered experiments, check their parameters, or create entirely new tracking entries. Data updates can be submitted via JSON format in the UI.

### 3. Collaborate on Plans
Go to the "Plan Collaboration" tab. Here you can establish overarching research goals and invite collaborators. You can also define sequential steps essential for experiment execution.

### 4. AI Interaction
Switch over to the "AI Research Assistant" to interact via text prompts. Supported system prompts include:
* `儀器使用 [Instrument Name]`
* `設計實驗流程 [Research Goal]`
* `拆分問題 [Research Question]`
* `標準流程 [Experiment Details]`

---

## Advanced Settings: Adding Instrument Documents

To enable customized instrument queries, place JSON-formatted instrument definition files in the `instrument_docs` folder located at the project's root.

**Example File Structure:** `instrument_docs/spectrometer.json`

```json
{
    "instrument_id": "inst_002",
    "name": "Spectrometer",
    "description": "An instrument to measure properties of light over a specific portion of the electromagnetic spectrum.",
    "guide": "spectrometer_guide.txt"
}
```
*Note: Make sure to also create the corresponding manual file (e.g., `spectrometer_guide.txt`) next to the configuration file.*

---

**LabMate AI - Simplifying research, empowering intelligence.**
