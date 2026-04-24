# Technical Specification: MDB Impact Dashboards (Streamlit Implementation)

This specification provides the logic, state management requirements, and component architecture for building a multi-role Impact Measurement and Monitoring (IMM) system. It is designed to be machine-readable for AI coding assistants and provides clear instructions for Streamlit specialists.

---

## 1. Global State & Data Architecture
To ensure seamless transitions between dashboards, the application must maintain a centralized `st.session_state`.

* **Indicator Catalog (Reference Data):** * Load the **HIPSO** and **FAST-Infra** indicator sets into a dictionary or `pd.DataFrame`.
    * Maintain a mapping of **Transition Qualities** (Competitive, Green, etc.) to their respective sub-dimensions and frontier gaps.
* **The Calculation Engine (`engine.py`):**
    * **ETI Formula:** `eti_score = country_gap_adjustment * project_intensity_sum`.
    * **AIMM Formula:** `total_aimm = (project_outcome * risk) + (market_outcome * risk)`.

---

## 2. Role: The Strategy Economist (Macro-Diagnostic View)
**Objective:** Visualize regional gaps to prioritize resource allocation.

### Streamlit Implementation Instructions:
* **Geospatial Layer:** Use `st.pydeck_chart` to render a Choropleth map.
    * **Color Scale:** Map `ATQ scores` (-10% to +10%) to a diverging color scale (Red to Green).
* **Gap Comparison Tool:**
    * Use `st.multiselect` to allow users to compare specific indicators like **Economic Complexity Index** or **Resolving Insolvency Score** across multiple countries.
    * Implement `st.plotly_chart` for radar charts comparing a country's current profile against the **Frontier Baseline** (e.g., Japan for complexity, US for insolvency).
* **Logic:** When a country is selected, filter the `st.session_state.active_gap` to adjust the baseline for all subsequent IO deal simulations.

---

## 3. Role: The Investment Officer (Deal Structuring View)
**Objective:** Simulate impact scenarios to maximize AIMM/ETI scores.

### Streamlit Implementation Instructions:
* **Dynamic Sector Form:**
    * Use `st.selectbox` for **Sector Framework Briefs (SFBs)**.
    * **Logic:** Based on the sector (e.g., Agribusiness), use a dictionary lookup to generate `st.slider` widgets for relevant **Intensity Indicators** (e.g., "Yield Increase %" or "Female Farmers Reached").
* **Strategic Uplift Matrix:**
    * Provide `st.checkbox` inputs for "Local Currency," "Equity," and "SME focus".
    * **Visual Feedback:** Use `st.metric` with the `delta` parameter to show how each toggle increases the **Expected Transition Impact (ETI)** score in real-time.
* **AIMM 2025/2026 Enhancement:**
    * Implement a 2D slider or quadrant picker for **Innovation vs. Scalability** to drive the Market Outcome score.

---

## 4. Role: The Portfolio Manager (Monitoring View)
**Objective:** Track "Target vs. Actual" variance across the active portfolio.

### Streamlit Implementation Instructions:
* **Performance Grid:** * Use `st.data_editor` to display **HIPSO** standard indicators.
    * Apply `st.column_config.ProgressColumn` to visualize "Actual MWh Generated" vs. "Target MWh".
* **Variance Analytics:**
    * Calculate `variance = (actual / target) - 1`.
    * **Conditional Formatting:** Highlight rows in Red where variance is negative and >15% to flag projects requiring intervention.
* **Portfolio Roll-up:** * Use `st.tabs` to aggregate impact by theme (e.g., total GHG reduced, total jobs created) using `st.bar_chart`.

---

## 5. Role: The Compliance Specialist (Labeling & Verification)
**Objective:** Audit projects against universal labels (FAST-Infra / Green).

### Streamlit Implementation Instructions:
* **FAST-Infra Matrix:**
    * Render the 14 criteria (Biodiversity, Anti-Corruption, etc.) as an interactive checklist.
    * **Validation Logic:** Use `st.error` to block "Label Generation" if any of the **Baseline Requirements** (IFC Performance Standards alignment) are unchecked.
* **Evidence Upload:**
    * Integrate `st.file_uploader` for specialists to attach proof of **Positive Contributions** beyond the baseline.
* **Thematic Badging:**
    * Upon validation, generate a visual "Label Badge" (e.g., "FAST-Infra Certified") that can be appended to the Project Summary PDF.

---

## Technical Summary for Developers

| Feature | Streamlit Component | Indicator Context |
| :--- | :--- | :--- |
| **Gap Adjustment** | `st.sidebar.slider` | Adjusts ETI based on ATQ frontier gap. |
| **Intensity Scoring** | `st.number_input` | Captures project-specific outputs (Yields, KWh, Jobs). |
| **System Simplification** | `st.radio` | Implements the 2-level risk grid (IFC 2025 Enhancement). |
| **Logic Chain** | `st.graphviz_chart` | Visualizes the "Theory of Change" (Outputs -> Outcomes -> Systemic Change). |
| **Data Export** | `st.download_button` | Generates the Impact Scorecard for Credit Committee review. |