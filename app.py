import streamlit as st
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
import time

# Google Sheets authentication
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("your-service-account-file.json", scope)
    client = gspread.authorize(creds)
    return client

# Read the data from the sheet
def get_data_from_google_sheets(sheet_name):
    client = authenticate_google_sheets()
    sheet = client.open("NCAA Basketball 2025").worksheet(sheet_name)
    data = pd.DataFrame(sheet.get_all_records())
    return data

# Calculate the projected points for each player
def calculate_points(predictions_df, results_df):
    # Initialize a column for the points
    predictions_df['Points'] = 0

    rounds = ['FR', 'SR', 'SS', 'EA', 'FF', 'C']
    points = {'FR': 1, 'SR': 2, 'SS': 4, 'EA': 8, 'FF': 16, 'C': 32}
    
    for round_code in rounds:
        round_games = results_df[results_df['GameCode'].str.startswith(round_code)]
        for index, game in round_games.iterrows():
            game_code = game['GameCode']
            winner = game['Winner']  # Winner of the game
            # Find the predictions for this game
            for player_index, player_row in predictions_df.iterrows():
                predicted_winner = player_row[game_code]  # Player's prediction for this game
                if predicted_winner == winner:
                    predictions_df.at[player_index, 'Points'] += points[round_code]
    return predictions_df

# Save the points projection to Google Sheets
def save_projection_to_google_sheets(df, sheet_name):
    client = authenticate_google_sheets()
    sheet = client.open("NCAA Basketball 2025").worksheet(sheet_name)
    sheet.clear()  # Clear the sheet before updating with new data
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# Plot the points evolution over time
def plot_points_evolution(points_history_df):
    plt.figure(figsize=(10, 6))
    for player in points_history_df.columns[1:]:
        plt.plot(points_history_df['Timestamp'], points_history_df[player], label=player)
    plt.xlabel('Timestamp')
    plt.ylabel('Points')
    plt.title('Evolution of Projected Points in Fantasy League')
    plt.legend(loc='upper left')
    st.pyplot()

# Streamlit app
def main():
    st.title("NCAA Basketball Fantasy League")

    # Load the results and player predictions
    results_df = get_data_from_google_sheets('Results')  # Results of games
    predictions_df = get_data_from_google_sheets('Predictions')  # Players' predictions
    points_history_df = get_data_from_google_sheets('Points History')  # Historical points data

    # Display the predictions dataframe
    st.subheader("Player Predictions")
    st.dataframe(predictions_df)

    # Evaluate the points based on current game results
    if st.button('Update Points'):
        predictions_df = calculate_points(predictions_df, results_df)
        st.subheader("Updated Points")
        st.dataframe(predictions_df[['Player', 'Points']])

        # Save the updated points
        save_projection_to_google_sheets(predictions_df, 'Predictions')

        # Save the points history with timestamp
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        points_history_df = points_history_df.append(pd.DataFrame([[timestamp] + predictions_df['Points'].tolist()]), ignore_index=True)
        save_projection_to_google_sheets(points_history_df, 'Points History')

        # Show the points evolution chart
        plot_points_evolution(points_history_df)

# Run the app
if __name__ == '__main__':
    main()
