import os
import re
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
import io
import shutil

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_super_secret_key')

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def extract_player_data_from_line(line):
    # Remove leading/trailing whitespace and pipes
    line = line.strip().strip('|').strip()
    # Split by pipe, allowing for any amount of whitespace around pipes
    cells = [cell.strip() for cell in re.split(r'\s*\|\s*', line)]
    if len(cells) < 7:
        return None
    try:
        return {
            'Rank': 0,
            'Player_Name': cells[1],
            'Team': cells[0],
            'Defeats': int(cells[2].replace(',', '')),
            'Assists': int(cells[3].replace(',', '')),
            'Damage_Dealt': int(cells[4].replace(',', '')),
            'Damage_Taken': int(cells[5].replace(',', '')),
            'Amount_Healed': int(cells[6].replace(',', ''))
        }
    except (ValueError, IndexError):
        return None

def parse_markdown_data(data_string):
    lines = data_string.strip().split('\n')
    records = []
    for line in lines:
        # Skip header and separator lines (flexible)
        if re.match(r'^\s*\|?\s*[-: ]+\|?$', line):
            continue
        record = extract_player_data_from_line(line)
        if record:
            records.append(record)
    if not records:
        raise ValueError("No valid player data rows found. Please ensure the data is in a markdown table format.")
    return pd.DataFrame(records)

def update_player_csv_data(player_df):
    stats = {'added': 0, 'duplicates': 0}
    unique_columns = ['Defeats', 'Assists', 'Damage_Dealt', 'Damage_Taken', 'Amount_Healed']
    for player_name, group_df in player_df.groupby('Player_Name'):
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', player_name)
        if not safe_name:
            continue
        file_path = os.path.join(DATA_DIR, f"{safe_name}.csv")
        try:
            existing_df = pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame()
        except pd.errors.EmptyDataError:
            existing_df = pd.DataFrame()
        combined_df = pd.concat([existing_df, group_df], ignore_index=True)
        updated_df = combined_df.drop_duplicates(subset=unique_columns, keep='first')
        original_rows = len(existing_df)
        new_total_rows = len(updated_df)
        stats['added'] += (new_total_rows - original_rows)
        stats['duplicates'] += (len(group_df) - (new_total_rows - original_rows))
        updated_df.to_csv(file_path, index=False)
    return stats

@app.route('/player_upload', methods=['GET', 'POST'])
def player_upload_page():
    if request.method == 'POST':
        data_string = request.form.get('markdown_data', '')
        file = request.files.get('file')
        if not data_string and not file:
            flash("No data or file provided.", 'warning')
            return redirect(url_for('player_upload_page'))
        try:
            if file and file.filename != '':
                data_string = file.read().decode('utf-8')
            player_data_df = parse_markdown_data(data_string)
            result_stats = update_player_csv_data(player_data_df)
            flash(
                f"Processing complete! Added: {result_stats['added']} new records. "
                f"Ignored: {result_stats['duplicates']} duplicate records.",
                'success'
            )
            return redirect(url_for('player_analysis_page'))
        except ValueError as e:
            flash(f"Error: {e}", 'danger')
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", 'danger')
    return render_template('player_upload.html')

@app.route('/clear_data', methods=['POST'])
def clear_data_page():
    try:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        os.makedirs(DATA_DIR, exist_ok=True)
        flash("All player data has been successfully cleared!", 'success')
    except Exception as e:
        flash(f"Failed to clear data: {e}", 'danger')
    return redirect(url_for('player_upload_page'))

@app.route('/guild_upload', methods=['GET', 'POST'])
def guild_upload_page():
    if request.method == 'POST':
        # Add guild upload logic here if needed
        flash("Guild data uploaded successfully!", "success")
        return redirect(url_for('guild_upload_page'))
    return render_template('guild_upload.html')

def get_all_player_data():
    all_dfs = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.csv'):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                df = pd.read_csv(file_path)
                if not df.empty:
                    all_dfs.append(df)
            except Exception:
                continue
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

@app.route('/player_analysis')
def player_analysis_page():
    all_players_df = get_all_player_data()
    players_list = []
    overall_averages = {}
    if not all_players_df.empty and 'Player_Name' in all_players_df.columns:
        summary_df = all_players_df.groupby('Player_Name').agg(
            Team=('Team', 'first'),
            Total_Defeats=('Defeats', 'sum'),
            Total_Assists=('Assists', 'sum'),
            Total_Damage_Dealt=('Damage_Dealt', 'sum'),
            Total_Games=('Player_Name', 'size')
        ).sort_values(by='Total_Defeats', ascending=False).reset_index()
        for col in ['Total_Defeats', 'Total_Assists', 'Total_Damage_Dealt']:
            summary_df[col] = summary_df[col].apply(lambda x: f"{x:,.0f}")
        players_list = summary_df.to_dict('records')
        # Calculate overall averages
        overall_averages = {
            'Avg_Defeats': all_players_df['Defeats'].mean(),
            'Avg_Assists': all_players_df['Assists'].mean(),
            'Avg_Damage_Dealt': all_players_df['Damage_Dealt'].mean()
        }
    return render_template('player_analysis.html', players=players_list, overall_averages=overall_averages)

@app.route('/player_details/<player_name>')
def player_details_page(player_name):
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', player_name)
    file_path = os.path.join(DATA_DIR, f"{safe_name}.csv")
    if not os.path.exists(file_path):
        flash(f"Player '{player_name}' not found.", 'danger')
        return redirect(url_for('player_analysis_page'))
    df = pd.read_csv(file_path)
    if df.empty:
        return redirect(url_for('player_analysis_page'))
    num_games = len(df)
    total_stats = {
        'Total_Games': num_games,
        'Total_Defeats': f"{df['Defeats'].sum():,.0f}",
        'Total_Assists': f"{df['Assists'].sum():,.0f}",
        'Total_Damage_Dealt': f"{df['Damage_Dealt'].sum():,.0f}",
        'Total_Damage_Taken': f"{df['Damage_Taken'].sum():,.0f}",
        'Total_Amount_Healed': f"{df['Amount_Healed'].sum():,.0f}",
    }
    average_stats = {
        'Avg_Defeats': f"{df['Defeats'].mean():,.2f}" if num_games > 0 else "0.00",
        'Avg_Assists': f"{df['Assists'].mean():,.2f}" if num_games > 0 else "0.00",
        'Avg_Damage_Dealt': f"{df['Damage_Dealt'].mean():,.2f}" if num_games > 0 else "0.00",
        'Avg_Damage_Taken': f"{df['Damage_Taken'].mean():,.2f}" if num_games > 0 else "0.00",
        'Avg_Amount_Healed': f"{df['Amount_Healed'].mean():,.2f}" if num_games > 0 else "0.00",
    }
    return render_template('player_details.html',
                           player_name=player_name,
                           total_stats=total_stats,
                           average_stats=average_stats)

@app.route('/')
def index():
    return redirect(url_for('player_analysis_page'))

if __name__ == '__main__':
    app.run(debug=True)