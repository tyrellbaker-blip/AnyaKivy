import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
#when i try to briefcase run the app i get an error that says "no module named pandas" even though it's installed

class QBStatsApp(toga.App):
    def startup(self):
        # Create the home screen
        self.home_screen = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Create the header
        header_label = toga.Label('Predict football', style=Pack(font_size=24))
        self.home_screen.add(header_label)
        # Create the description
        description_label = toga.Label(
            'Welcome to Predict Football. Predict Football is a revolutionary football app that predicts next season\'s '
            'statistics for 74 different active quarterbacks. Predict Football helps its users primarily with fantasy '
            'football drafting, however it can also be used as a tool for sports betting and other football related '
            'endeavors!\n\nOur projected fantasy points are calculated using ESPN\'s model.',
            style=Pack(font_size=12)
        )
        self.home_screen.add(description_label)

        # Create the search button
        search_button = toga.Button('Search', on_press=self.open_search_page, style=Pack(padding=10))
        self.home_screen.add(search_button)

        # Create the players button

        # Create the main window
        self.main_window = toga.MainWindow(title='Predict Football', size=(800, 600))
        self.main_window.content = self.home_screen
        self.main_window.show()

    def open_search_page(self, widget):
        # Create the search page
        search_page = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Create the search box
        search_label = toga.Label('Enter the name of a Quarterback: ')
        self.search_input = toga.TextInput()
        search_button = toga.Button('Search', on_press=self.search_quarterback)

        search_box = toga.Box(style=Pack(direction=ROW, padding=10))
        search_box.add(search_label)
        search_box.add(self.search_input)
        search_box.add(search_button)

        search_page.add(search_box)

        # Create the search result table
        self.table = toga.Table(
            headings=['Team', 'Player', 'Pass Yds 2023-24', 'TD 2023-24', 'INT 2023-24',
                      'Comp 2023-24', 'Att 2023-24', 'QBR', 'Fantasy Points'],
            data=[],
            style=Pack(flex=1)
        )

        search_page.add(self.table)

        # Create the back button
        back_button = toga.Button('Back', on_press=self.back_to_home, style=Pack(padding=10))
        search_page.add(back_button)

        # Update the main window content to the search page
        self.main_window.content = search_page

    def back_to_home(self, widget):
        # Reset the search input and table data
        self.search_input.value = ''
        self.table.data = []

        # Show the home screen
        self.main_window.content = self.home_screen


    def search_quarterback(self, widget):
        # Get the search query
        search_query = self.search_input.value.strip().lower()

        # Load data
        url = "https://raw.githubusercontent.com/anyaa07/QBs/main/QB20.csv"
        url2 = "https://raw.githubusercontent.com/anyaa07/QBs/main/QB21.csv"
        url3 = "https://raw.githubusercontent.com/anyaa07/QBs/main/QB22.csv"

        QB20 = pd.read_csv(url)
        QB21 = pd.read_csv(url2)
        QB22 = pd.read_csv(url3)

        # Assign weights to each DataFrame
        weight_20 = 0.5  # Weight for QB20
        weight_21 = 1.5  # Weight for QB21
        weight_22 = 1.5  # Weight for QB22

        # Add weight columns to each DataFrame
        QB20['Weight'] = weight_20
        QB21['Weight'] = weight_21
        QB22['Weight'] = weight_22

        pd.set_option('display.max_rows', None)

        # Merge data
        QB21_2 = QB21.rename(columns={'Pass': 'Pass Yds', 'TD2': 'TD', 'INT2': 'INT', 'Att2': 'Att',
                                      'Comp2': 'Comp', 'Year2': 'Year'})
        QB20_2 = QB20.rename(columns={'TDs': 'TD', 'INTs': 'INT', 'Year3': 'Year'})
        merged = pd.concat([QB20_2, QB22], axis=0, ignore_index=True)
        merged2 = pd.concat([QB21_2, QB22], axis=0, ignore_index=True)
        data = pd.merge(QB20, QB21, on=['Player', 'Team'])
        data1 = pd.merge(data, QB22, on=['Player', 'Team'])

        # Create linear regression model
        model = LinearRegression()  # You can adjust the alpha parameter
        predicted_stats = []

        # Loop through each player
        for player in data1['Player'].unique():
            # Fit model to player data, merge 20 and 21 for x, 21 and 22 for y
            X = merged[['Pass Yds', 'TD', 'INT', 'Comp', 'Att']]
            y = merged2[['Pass Yds', 'TD', 'INT', 'Comp', 'Att']]
            sample_weights_X = QB20['Weight'].values  # Weight for QB20 data
            sample_weights_y = QB22['Weight'].values  # Weight for QB22 data
            sample_weights = np.concatenate((sample_weights_X, sample_weights_y))
            model.fit(X, y, sample_weight=sample_weights)

            # Predict 2023-24 season stats
            predicted_stat = model.predict(QB22[['Pass Yds', 'TD', 'INT', 'Comp', 'Att']])
            predicted_stats.append(predicted_stat)

        # Assign predicted statistics to the corresponding columns
        pass_yd_pts = 0.04
        pass_td_pts = 4
        int_pts = -2
        for index, player in enumerate(data1['Player'].unique()):
            mask = (data1['Player'] == player)
            data1.loc[mask, 'Pass Yds_2023_24'] = predicted_stats[index][0][0]
            data1.loc[mask, 'TD_2023_24'] = predicted_stats[index][0][1]
            data1.loc[mask, 'INT_2023_24'] = predicted_stats[index][0][2]
            data1.loc[mask, 'Comp_2023_24'] = predicted_stats[index][0][3]
            data1.loc[mask, 'Att_2023_24'] = predicted_stats[index][0][4]

            # Calculate fantasy points
            fantasy_points = (data1['Pass Yds_2023_24'] * pass_yd_pts +
                              data1['TD_2023_24'] * pass_td_pts +
                              data1['INT_2023_24'] * int_pts)
            data1.loc[mask, 'Fantasy_Points'] = fantasy_points

        # QBR Calculation
        cp = (data1['Comp_2023_24'] / data1['Att_2023_24'] - 0.3) * 0.05
        ypa = (data1['Pass Yds_2023_24'] / data1['Att_2023_24'] - 3) * 0.25
        tdp = (data1['TD_2023_24'] / data1['Att_2023_24']) * 0.2
        intp = (data1['INT_2023_24'] / data1['Att_2023_24']) * 0.25

        data1['QBR'] = ((data1['Comp_2023_24'] - 30) / 20 +
                        ((data1['Pass Yds_2023_24'] / data1['Att_2023_24']) - 3) * 0.25 +
                        (data1['TD_2023_24']) * 0.2 + 2.375 - (data1['INT_2023_24'] * 0.25)) * 100 / 6 / 3

        # Filter results based on search query
        filtered_data = data1[data1['Player'].str.lower().str.contains(search_query)]

        # Update the search result table
        self.table.data = filtered_data[['Team', 'Player', 'Pass Yds_2023_24', 'TD_2023_24', 'INT_2023_24',
                                         'Comp_2023_24', 'Att_2023_24', 'QBR', 'Fantasy_Points']].values.tolist()


def main():
    app = QBStatsApp('QB Stats Application', 'com.example.qbstats')
    return app


if __name__ == '__main__':
    main().main_loop()