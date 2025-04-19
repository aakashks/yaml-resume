#!/usr/bin/env python3
"""
Resume Generator - Convert YAML resume to LaTeX PDF

This script reads resume data from a YAML file (following JSON Resume schema)
and renders it using a Jinja2 LaTeX template to create a PDF resume.

Usage:
    python generate.py --yaml cv.yaml --template template.tex.j2 --output cv.pdf
"""

import argparse
import os
import subprocess
import yaml
from jinja2 import Environment, FileSystemLoader
import re
from datetime import datetime

def load_yaml_data(yaml_file):
    """Load resume data from YAML file."""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return None


def format_dates(obj):
    """Recursively convert YYYY-MM strings to 'Mon YYYY' in all strings in the given object (dict, list, or str)."""
    date_pattern = re.compile(r'^(\d{4})-(\d{2})$')
    if isinstance(obj, str):
        match = date_pattern.match(obj)
        if match:
            year, month = match.groups()
            try:
                dt = datetime.strptime(obj, "%Y-%m")
                return dt.strftime("%b %Y")
            except Exception:
                return obj
        return obj
    elif isinstance(obj, list):
        return [format_dates(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: format_dates(v) for k, v in obj.items()}
    else:
        return obj

def escape_percent(obj):
    """Recursively escape % as \% in all strings in the given object (dict, list, or str)."""
    if isinstance(obj, str):
        return obj.replace('%', r'\%')
    elif isinstance(obj, list):
        return [escape_percent(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: escape_percent(v) for k, v in obj.items()}
    else:
        return obj
    
def escape_ampersand(obj):
    """Recursively escape & as \& in all strings in the given object (dict, list, or str)."""
    if isinstance(obj, str):
        return obj.replace('&', r'\&')
    elif isinstance(obj, list):
        return [escape_ampersand(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: escape_ampersand(v) for k, v in obj.items()}
    else:
        return obj

def render_template(template_file, data):
    """Render Jinja2 template with resume data."""
    try:
        # Get the directory containing the template
        template_dir = os.path.dirname(os.path.abspath(template_file))
        template_name = os.path.basename(template_file)
        
        # Create Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(template_dir),
            block_start_string='((%',
            block_end_string='%))',
            variable_start_string='((',
            variable_end_string='))',
            comment_start_string='((#',
            comment_end_string='#))',
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load template
        template = env.get_template(template_name)
        
        # Format dates in all data values
        formatted_data = format_dates(data)
        # Escape % in all data values
        safe_data = escape_percent(formatted_data)
        # Escape & in all data values
        safe_data = escape_ampersand(safe_data)
        # Render template with data
        rendered = template.render(**safe_data)
        return rendered
    except Exception as e:
        print(f"Error rendering template: {e}")
        return None


def compile_latex(tex_content, output_file):
    """Compile LaTeX content to PDF."""
    # Create a temporary .tex file
    temp_tex = "temp.tex"
    try:
        with open(temp_tex, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        
        # Run pdflatex twice to resolve references
        subprocess.run(['pdflatex', '-interaction=nonstopmode', temp_tex], check=True)
        subprocess.run(['pdflatex', '-interaction=nonstopmode', temp_tex], check=True)
        
        # Rename the output file if needed
        if output_file != "temp.pdf":
            os.rename("temp.pdf", output_file)
            
        # Clean up temporary files
        for ext in ['.aux', '.log', '.out', '.tex', '.fls', '.fdb_latexmk']:
            if os.path.exists(f"temp{ext}"):
                os.remove(f"temp{ext}")
                
        print(f"CV successfully generated: {output_file}")
        return True
    except subprocess.CalledProcessError:
        print("Error compiling LaTeX document. Check LaTeX installation or template syntax.")
        return False
    except Exception as e:
        print(f"Error during compilation: {e}")
        return False


def main():
    """Main function to process resume."""
    parser = argparse.ArgumentParser(description='Generate PDF resume from YAML data using LaTeX template.')
    parser.add_argument('--yaml', required=True, help='Path to YAML resume file')
    parser.add_argument('--template', required=True, help='Path to Jinja LaTeX template')
    parser.add_argument('--output', default='cv.pdf', help='Output PDF filename')
    args = parser.parse_args()
    
    # Load resume data
    resume_data = load_yaml_data(args.yaml)
    if not resume_data:
        return
    
    # Render LaTeX template
    latex_content = render_template(args.template, resume_data)
    if not latex_content:
        return
    
    # Compile to PDF
    compile_latex(latex_content, args.output)


if __name__ == "__main__":
    main()
