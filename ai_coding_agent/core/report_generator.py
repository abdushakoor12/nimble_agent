"""Converts logs into a human-readable HTML report."""

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def format_json(obj: Any, indent: int = 0) -> str:
    """Format JSON content for HTML display with proper indentation and structure."""
    if isinstance(obj, dict | list):
        if isinstance(obj, dict):
            items = [
                f'<div class="json-line" style="margin-left: {indent}px">'
                f'<span class="json-key">"{k}"</span><span class="json-punctuation">: </span>{format_json(v, indent + 20)}</div>'
                for k, v in obj.items()
            ]
            return f"""<div class="json-object"><span class="json-punctuation">{"{"}</span>{"".join(items)}<span class="json-punctuation">{"}"}</span></div>"""
        else:  # list
            items = [
                f'<div class="json-line" style="margin-left: {indent}px">'
                f"{format_json(item, indent + 20)}</div>"
                for item in obj
            ]
            return f"""<div class="json-array"><span class="json-punctuation">[</span>{"".join(items)}<span class="json-punctuation">]</span></div>"""
    elif isinstance(obj, str):
        return f'<span class="json-string">"{obj}"</span>'
    elif isinstance(obj, bool):
        return f'<span class="json-boolean">{str(obj).lower()}</span>'
    elif obj is None:
        return '<span class="json-null">null</span>'
    else:
        return f'<span class="json-number">{obj}</span>'


def generate_html_report(source_filename: str, output_filename: str) -> None:
    """Generate an HTML report from the JSON log file sorted by timestamp."""
    # Read and parse the JSON log file
    log_dir = "logs/logs"
    log_path = os.path.join(log_dir, os.path.basename(source_filename))

    with open(log_path) as log_file:
        log_entries = [json.loads(line) for line in log_file]

    # Sort log entries by timestamp
    log_entries.sort(
        key=lambda entry: datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
    )

    # Generate modern HTML content with improved readability
    html_content = (
        """
    <html>
    <head>
        <title>"""
        + source_filename
        + """</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f9;
                line-height: 1.6;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px;
                background-color: #fff;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                font-weight: 600;
                color: #1a1a1a;
                margin: 0;
            }
            .log-entry {
                border: 1px solid #e4e4e7;
                margin-bottom: 16px;
                border-radius: 12px;
                background-color: #fafafa;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
                overflow: hidden;
            }
            .entry-header {
                padding: 16px 24px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #fff;
                transition: background-color 0.2s ease;
            }
            .entry-header:hover {
                background-color: #f8fafc;
            }
            .header-content {
                display: flex;
                align-items: center;
                gap: 16px;
                flex: 1;
            }
            .expand-icon {
                width: 20px;
                height: 20px;
                color: #64748b;
                transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                transform-origin: center;
            }
            .expand-icon svg {
                width: 100%;
                height: 100%;
            }
            .entry-content.active + .expand-icon {
                transform: rotate(180deg);
            }
            .entry-content {
                max-height: 0;
                padding: 0 24px;
                overflow: hidden;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .timestamp {
                font-weight: 500;
                color: #374151;
                font-size: 0.9rem;
                margin-bottom: 8px;
            }
            .level {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 6px;
                margin: 8px 0;
                font-weight: 500;
                font-size: 0.875rem;
            }
            .level.INFO { background-color: #dbeafe; color: #1e40af; }
            .level.ERROR { background-color: #fee2e2; color: #b91c1c; }
            .level.WARNING { background-color: #fff7ed; color: #c2410c; }
            .name {
                font-size: 0.9rem;
                color: #4b5563;
                margin: 8px 0;
            }
            .message {
                margin: 16px 0;
                padding: 16px;
                background-color: #fff;
                border-left: 4px solid #3b82f6;
                white-space: pre-wrap;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.9rem;
                line-height: 1.5;
                border-radius: 0 6px 6px 0;
            }
            .metadata {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 12px;
                margin: 16px 0;
            }
            .metadata-item {
                background-color: #f3f4f6;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.875rem;
                color: #374151;
            }
            .collapsible {
                background-color: #f8fafc;
                color: #475569;
                cursor: pointer;
                padding: 12px 16px;
                width: 100%;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                text-align: left;
                outline: none;
                font-size: 0.875rem;
                font-weight: 500;
                margin-top: 16px;
                transition: all 0.2s ease;
            }
            .collapsible:hover {
                background-color: #f1f5f9;
            }
            .content {
                max-height: 0;
                padding: 0 16px;
                overflow: hidden;
                background-color: #ffffff;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .content.active {
                max-height: 2000px;
                padding: 16px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin-top: 8px;
            }
            .json-content {
                background-color: #1e1e1e;
                padding: 16px;
                border-radius: 8px;
                margin: 12px 0;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem;
                line-height: 1.6;
                color: #d4d4d4;
                max-height: 800px;
                overflow-y: auto;
                overflow-x: auto;
            }
            .json-key { color: #9cdcfe; }
            .json-string { color: #ce9178; }
            .json-number { color: #b5cea8; }
            .json-boolean { color: #569cd6; }
            .json-null { color: #569cd6; }
            .json-punctuation { color: #d4d4d4; }
            .json-line {
                padding: 2px 0;
            }
            .json-object, .json-array {
                margin: 4px 0;
            }
            .args-section {
                margin: 16px 0;
                background-color: #1e1e1e;
                border-radius: 8px;
                overflow: hidden;
            }
            .args-section h3 {
                color: #d4d4d4;
                margin: 0;
                padding: 16px;
                background-color: #252526;
                font-size: 0.9rem;
                font-weight: 500;
            }
        </style>
        <script>
            function toggleContent(id) {
                var content = document.getElementById(id);
                var header = content.previousElementSibling;
                var icon = header.querySelector('.expand-icon');

                if (content.classList.contains('active')) {
                    content.classList.remove('active');
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    content.classList.add('active');
                    icon.style.transform = 'rotate(180deg)';
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>"""
        + output_filename
        + """</h1>
            </div>
    """
    )

    for _i, entry in enumerate(log_entries):
        # Use the format_log_entry function to generate the HTML for each log entry
        html_content += format_log_entry(entry)

    html_content += """
        </div>
    </body>
    </html>
    """

    # Ensure directories exist
    report_dir = "logs/reports"
    os.makedirs(report_dir, exist_ok=True)

    # Write the HTML report to logs/reports
    html_filename = os.path.join(report_dir, output_filename)
    with open(html_filename, "w") as html_file:
        html_file.write(html_content)

    logger.info(f"HTML report generated: {html_filename}")


def get_level_class(level: str) -> str:
    """Get the CSS class for a log level."""
    level_map = {
        "ERROR": "error",
        "WARNING": "warning",
        "INFO": "info",
        "DEBUG": "debug",
    }
    return level_map.get(level, "info")


def format_log_entry(entry: dict[str, Any]) -> str:  # noqa: C901
    """Format a log entry as HTML."""
    level_class = get_level_class(entry.get("levelname", "INFO"))
    is_debug = entry.get("levelname") == "DEBUG"
    entry_id = hash(entry.get("msg", "") + entry["timestamp"])

    # Header content that's always visible
    main_content = f"""
        <div class="log-entry {level_class}">
            <div class="entry-header" onclick="toggleContent('entry-{entry_id}')">
                <div class="header-content">
                    <div class="timestamp">{entry.get("timestamp", "")}</div>
                    <div class="level {level_class}">{entry.get("levelname", "INFO")}</div>
                    <div class="name">{entry.get("function_name")} - ({entry.get("name", "")})</div>
                </div>
                <div class="expand-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
            </div>
            <div class="content entry-content {"active" if not is_debug else ""}" id="entry-{entry_id}">"""

    # Add metadata
    main_content += '<div class="metadata">'
    important_fields = ["function_name", "module", "lineno"]
    for field in important_fields:
        if field in entry:
            main_content += f'<div class="metadata-item">{field}: {entry[field]}</div>'
    main_content += "</div>"

    # Show template (msg) in the main panel
    if "msg" in entry:
        main_content += f'<div class="message">{entry["msg"]}</div>'

    # Check if we have LLM response data in args
    has_llm_response = False
    if entry.get("args"):
        args = entry["args"]
        if isinstance(args, list) and len(args) > 0 and isinstance(args[0], dict):
            first_arg = args[0]
            if "generations" in first_arg:
                has_llm_response = True
                main_content += '<div class="args-section"><h3>LLM Response</h3>'
                main_content += (
                    f'<div class="json-content">{format_json(first_arg)}</div></div>'
                )

    # Show args in the main panel if present and not an LLM response or chat model start
    is_chat_model_start = entry.get("function_name") == "on_chat_model_start"
    if (
        "args" in entry
        and entry["args"]
        and not has_llm_response
        and not is_chat_model_start
    ):
        main_content += f'<div class="json-content">{format_json(entry["args"])}</div>'

    # Add any additional fields to the collapsible section
    verbose_content = ""
    for key, value in entry.items():
        if key == "args" and is_chat_model_start:
            verbose_content += f'<div class="json-content">{format_json(value)}</div>'
        elif isinstance(value, dict | list):
            verbose_content += f'<div class="json-content">{format_json(value)}</div>'
        else:
            verbose_content += f'<div class="metadata-item">{key}: {value}</div>'

    if verbose_content:
        main_content += f"""
        <button class="collapsible" onclick="toggleContent('content-{entry_id}')">Show additional details</button>
        <div class="content" id="content-{entry_id}">
            {verbose_content}
        </div>"""

    main_content += "</div></div>"
    return main_content
