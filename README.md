# SAGE - Research Report Generator

SAGE is a research report generation tool that uses AI to produce comprehensive reports on any given topic. It leverages natural language processing models to create AI analyst personas, conduct interviews, gather contextual data, and finally compile reports with introductions, conclusions, and detailed content sections.

You can access the live demo of this application [here](https://sage-master.streamlit.app/).

## Features

- **AI Analyst Personas:** Automatically generates multiple AI personas to provide diverse perspectives on the topic.
- **Automated Interviews:** Conducts AI-driven interviews with each analyst based on the topic, gathering insights and summaries.
- **Integrated Search Results:** Uses external search tools and Wikipedia to enrich the report content with relevant, up-to-date information.
- **Automated Report Generation:** Automatically structures the report by writing the introduction, body, and conclusion based on the collected data.
- **Streamlined Workflow:** Each step in the report generation process is represented as nodes in a directed graph, ensuring an efficient and clear research flow.

## How It Works

1. **Input a Topic:** The user provides a topic for the research report.
2. **Generate Analysts:** The application creates 3 distinct AI analyst personas to discuss the topic.
3. **Conduct Interviews:** Each analyst "interviews" on the topic by generating relevant questions, searching for answers, and summarizing their insights.
4. **Generate Report:** The sections from the interviews are compiled into a comprehensive report, along with an introduction and conclusion.
5. **Final Report:** The complete report is displayed to the user.

## Code Structure

- **Main Components:**
  - `ChatGroq`: A language model used for generating AI-driven conversations and content.
  - `TavilySearchResults`: A search tool for fetching relevant external data to enrich the report.
  - `WikipediaLoader`: Extracts Wikipedia data based on the search query.
  
- **Key Functions:**
  - `create_analysts()`: Generates AI personas based on the provided topic.
  - `conduct_interview()`: Conducts interviews by generating questions and gathering answers using search tools and Wikipedia.
  - `write_report()`: Compiles all the interview sections into a cohesive report.
  - `write_intro_conclusion()`: Automatically writes the introduction and conclusion for the report.
  - `finalize_report()`: Combines the introduction, body, and conclusion into the final report format.
  - `build_research_graph()`: Constructs a state graph for the research workflow, connecting various stages from analyst creation to report finalization.

- **State Management:**
  The research process is modeled using a state graph that tracks the progress of report generation. This includes the current analyst, sections written, and report status.
