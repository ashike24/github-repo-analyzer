import streamlit as st
import json
import pandas as pd
from analyzer import GitHubAnalyzer

st.set_page_config(page_title="GitHub Repository Intelligence Analyzer", layout="wide")

st.title("GitHub Repository Intelligence Analyzer")
st.markdown("Analyze multiple GitHub repositories and get insights about their activity, complexity, and learning difficulty.")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("GitHub Personal Access Token (optional but recommended)", type="password", help="Increases rate limit from 60 to 5000 requests/hour")
    st.markdown("---")
    st.markdown("**Scoring Formula**")
    st.markdown("**Activity Score (0-100)**")
    st.markdown("- Stars: 20%\n- Forks: 15%\n- Commits: 25%\n- Contributors: 20%\n- Recency: 20%")
    st.markdown("**Complexity Score (0-100)**")
    st.markdown("- Languages: 25%\n- File count: 35%\n- Dependency files: 20%\n- Commit history: 20%")
    st.markdown("**Difficulty**")
    st.markdown("- Beginner: combined < 30\n- Intermediate: 30-60\n- Advanced: > 60")

st.subheader("Enter GitHub Repository URLs")
urls_input = st.text_area(
    "One URL per line",
    placeholder="https://github.com/owner/repo\nhttps://github.com/owner/repo2",
    height=150
)

if st.button("Analyze Repositories", type="primary"):
    urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]
    if not urls:
        st.warning("Please enter at least one repository URL.")
    else:
        analyzer = GitHubAnalyzer(token=token if token else None)
        results = []
        errors = []

        progress = st.progress(0)
        status = st.empty()

        for i, url in enumerate(urls):
            status.text(f"Analyzing {url} ...")
            result = analyzer.analyze(url)
            if "error" in result:
                errors.append(result)
            else:
                results.append(result)
            progress.progress((i + 1) / len(urls))

        status.text("Done!")

        if errors:
            st.error("Some repositories could not be analyzed:")
            for e in errors:
                st.write(e)

        if results:
            st.subheader("Summary Table")
            df = pd.DataFrame([{
                "Repository": r["repo"],
                "Stars": r["stars"],
                "Forks": r["forks"],
                "Commits": r["commit_count"],
                "Contributors": r["contributor_count"],
                "Languages": r["language_count"],
                "Activity Score": r["activity_score"],
                "Complexity Score": r["complexity_score"],
                "Difficulty": r["difficulty"],
            } for r in results])

            def color_difficulty(val):
                colors = {"Beginner": "background-color: #d4edda", "Intermediate": "background-color: #fff3cd", "Advanced": "background-color: #f8d7da"}
                return colors.get(val, "")

            styled_df = df.style.applymap(color_difficulty, subset=["Difficulty"])
            st.dataframe(styled_df, use_container_width=True)

            st.subheader("Detailed Reports")
            for r in results:
                with st.expander(f"{r['repo']} — {r['difficulty']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Activity Score", f"{r['activity_score']}/100")
                        st.metric("Stars", r["stars"])
                        st.metric("Forks", r["forks"])
                        st.metric("Open Issues", r["open_issues"])
                    with col2:
                        st.metric("Complexity Score", f"{r['complexity_score']}/100")
                        st.metric("Commits", r["commit_count"])
                        st.metric("Contributors", r["contributor_count"])
                        st.metric("Files", r["file_count"])
                    with col3:
                        st.metric("Difficulty", r["difficulty"])
                        st.metric("Languages", r["language_count"])
                        st.metric("Days Since Update", r["days_since_update"])
                        st.metric("Dependency Files", r["dependency_files"])

                    st.markdown(f"**Description:** {r['description']}")
                    st.markdown(f"**Languages:** {', '.join(r['languages']) if r['languages'] else 'None'}")
                    st.markdown(f"**License:** {r['license']}")
                    st.markdown(f"**Archived:** {'Yes' if r['is_archived'] else 'No'}")
                    if r["topics"]:
                        st.markdown(f"**Topics:** {', '.join(r['topics'])}")

            st.subheader("Download Report")
            report_json = json.dumps(results, indent=2)
            st.download_button(
                label="Download Full Report (JSON)",
                data=report_json,
                file_name="github_analysis_report.json",
                mime="application/json"
            )

            report_csv = df.to_csv(index=False)
            st.download_button(
                label="Download Summary (CSV)",
                data=report_csv,
                file_name="github_analysis_summary.csv",
                mime="text/csv"
            )
