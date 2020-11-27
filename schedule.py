import datetime
import requests
import time
import json

from bs4 import BeautifulSoup

import random
import xlrd
import xlsxwriter


def get_lookup_flights():
    wb = xlrd.open_workbook("OAG2018APCodeIndex.xlsx")
    xl_sheet = wb.sheet_by_name(wb.sheet_names()[0])

    lookup_flights = []
    for row_idx in range(2107, 2588):  # Iterate through rows
        airline = xl_sheet.cell(row_idx, 3).value
        flight_no = int(xl_sheet.cell(row_idx, 4).value)
        lookup_flights.append({
            'flight': f'{airline}{flight_no}',
            'from': xl_sheet.cell(row_idx, 1).value,
            'to': xl_sheet.cell(row_idx, 2).value
        })

    lookup_flights = [dict(s) for s in set(frozenset(d.items()) for d in lookup_flights)]

    for row_idx in range(2107, 2588):
        airline = xl_sheet.cell(row_idx, 3).value
        flight_no = int(xl_sheet.cell(row_idx, 4).value)
        fr = xl_sheet.cell(row_idx, 1).value
        to = xl_sheet.cell(row_idx, 2).value
        flight = f"{airline}{flight_no}"

        for fl in lookup_flights:
            if fl['flight'] == flight and fl['from'] == fr and fl['to'] == to:
                fl['ACType'] = xl_sheet.cell(row_idx, 7).value
                fl['deltaArrDay'] = int(xl_sheet.cell(row_idx, 11).value)
                fl['seats'] = int(xl_sheet.cell(row_idx, 12).value)
                fl['freight'] = xl_sheet.cell(row_idx, 13).value

    return lookup_flights


def write_to_excel(lookup_flights):
    workbook = xlsxwriter.Workbook('Auxiliary_Result.xlsx')
    new_worksheet = workbook.add_worksheet('Auxiliary Sheet')

    new_worksheet.write(0, 0, "FlightID")
    new_worksheet.write(0, 1, "Origin")
    new_worksheet.write(0, 2, "Destination")
    new_worksheet.write(0, 3, "Airline")
    new_worksheet.write(0, 4, "FlightNo")
    new_worksheet.write(0, 5, "fromDate")
    new_worksheet.write(0, 6, "toDate")
    new_worksheet.write(0, 7, "ACType")
    new_worksheet.write(0, 8, "daysofweek")
    new_worksheet.write(0, 9, "deptime")
    new_worksheet.write(0, 10, "arrtime")
    new_worksheet.write(0, 11, "deltaArrDay")
    new_worksheet.write(0, 12, "Seats")
    new_worksheet.write(0, 13, "Freight")

    row = 1
    col = 0
    for flight in lookup_flights:
        new_worksheet.write(row, col, 'new')
        new_worksheet.write(row, col + 1, flight['from'])
        new_worksheet.write(row, col + 2, flight['to'])
        new_worksheet.write(row, col + 3, flight['flight'][0:2])
        new_worksheet.write_number(row, col + 4, int(flight['flight'][2:]))
        new_worksheet.write_datetime(row, col + 5, flight['fromDate'])
        new_worksheet.write_datetime(row, col + 6, flight['toDate'])
        new_worksheet.write(row, col + 7, flight['ACType'])
        new_worksheet.write(row, col + 8, flight['daysOfWeek'])
        new_worksheet.write(row, col + 9, flight['deptime'])
        new_worksheet.write(row, col + 10, flight['arrtime'])
        new_worksheet.write(row, col + 11, flight['deltaArrDay'])
        new_worksheet.write(row, col + 12, flight['seats'])
        new_worksheet.write_number(row, col + 13, float(flight['freight']))
        row += 1
    workbook.close()


def convert_date(date):
    components = date.split(' ')
    months = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }
    for comp in components:
        if not comp:
            print('REMOVING!!!!')
            components.remove(comp)
    print(components)
    return f"{components[0]}-{months[components[1]]}-{components[2]}"


if __name__ == '__main__':
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    with open('flights_result_processing.json', mode='w', encoding='utf-8') as f:
        json.dump([], f)

    lookup_flights = get_lookup_flights()
    print(lookup_flights)

    # [
    #     {'from': 'PDX', 'flight': 'AS2348', 'to': 'SFO', 'ACType': '73H', 'deltaArrDay': 0, 'seats': 175, 'freight': 8.69999980926514}#,
    #    # {'flight': 'AS2507', 'from': 'BOI', 'to': 'PDX', 'ACType': 'DH4', 'deltaArrDay': 0, 'seats': 76, 'freight': 2.09999990463257}
    # ]

    for lookup_flight in lookup_flights:
        flights = []
        ind = 0
        print(f'At flight {lookup_flight}')
        for month in months:
            print(f'At month {month}')
            my_session = requests.session()
            for_cookies = my_session.get("https://www.cubesmart.com")
            cookies = for_cookies.cookies
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'}
            url = f'https://www.flightera.net/en/flight/United+Airlines-Portland-San+Francisco/{lookup_flight["flight"]}/{month}-2018'
            webContent = my_session.get(url=url, headers=headers, cookies=cookies)
            print(webContent)
            soup = BeautifulSoup(webContent.content, 'html.parser')

            classes = soup.findAll("tr", {"class": "my-2 mx-3 bg-white"})
            for element in classes:
                flight_info = element.findAll("td", {"class": "py-1 px-1 align-middle"})

                # First column
                first_column = flight_info[0]
                departure_date = first_column.findAll("a")[1]

                # Second column
                second_column = flight_info[1]
                spans = second_column.findAll("span", {"class": "text-nowrap"})
                origin_airport = spans[4]
                departure_time = spans[5]

                # Third column
                third_column = flight_info[2]
                spans = third_column.findAll("span", {"class": "text-nowrap"})
                destination_airport = spans[2]
                arrival_time = spans[3]

                flights.append({
                    'date': datetime.datetime.strptime(
                        convert_date(departure_date.getText().replace("\n", "").replace(".", "")), '%d-%m-%Y'),
                    'origin_airport': origin_airport.getText().split("/")[0].replace("(", "").strip(),
                    'destination_airport': destination_airport.getText().split("/")[0].replace("(", "").strip(),
                    'departure_time': departure_time.getText().replace("\n", "")[0:5],
                    'arrival_time': arrival_time.getText().replace("\n", "")[0:5]
                })

            if ind % 2 == 0:
                time.sleep(random.randint(45,60))
            else:
                time.sleep(random.randint(30,45))
            ind += 1

        data = flights
        new_data = []

        # with open('flights.json') as f:
        #     data = json.load(f)

        for flight in data:
            print(f'flight is {flight}')
            print(f'lookup flight is {lookup_flight}')
            # Remove extra flights
            if flight['origin_airport'] == lookup_flight['from'] and flight['destination_airport'] == lookup_flight['to']:
                new_data.append(flight)
            else:
                print(f'HERE!!!!!!!!!!!!!')
                print(flight['origin_airport'])
                print(flight['destination_airport'])

        data = new_data
        scheduled_times = {}
        for flight in data:
            dict_key = f'{flight["departure_time"]}-{flight["arrival_time"]}'
            if dict_key not in scheduled_times:
                scheduled_times[dict_key] = []

            # splitstr = flight['date'][0:10].split("-")
            # date = f'{splitstr[2]}-{splitstr[1]}-{splitstr[0]}'
            # flight['date'] = datetime.datetime.strptime(date, '%d-%m-%Y')
            scheduled_times[dict_key].append(flight['date'])

        new_result = {}
        for interval, dates in scheduled_times.items():
            # Minimum 2 dates
            if len(dates) >= 2:
                print(interval)
                print(dates)
                dates.sort()

                cutoffs = [0]
                for index, d in enumerate(dates):
                    # print(type(d))
                    if index != 0 and (d - last_date).days > 7:
                        cutoffs.append(index)
                    last_date = d

                new_dates = []
                for index, cutoff in enumerate(cutoffs):
                    if index == len(cutoffs) - 1:
                        new_dates.append(dates[cutoff:len(dates)])
                    else:
                        new_dates.append(dates[cutoff: cutoffs[index+1]])

                print(f'new dates are {new_dates}')

                for dates in new_dates:
                    # Determine daysOfWeek
                    days_of_week = []
                    for date in dates:
                        if type(date) == str:
                            splitstr = date[0:10].split("-")
                            date = f'{splitstr[2]}-{splitstr[1]}-{splitstr[0]}'
                            date = datetime.datetime.strptime(date, '%d-%m-%Y')
                        days_of_week.append(date.weekday() + 1)

                    print(days_of_week)
                    days_of_week.sort()
                    set_days_of_week = set(days_of_week)
                    str_days_of_week = ''
                    for el in set_days_of_week:
                        str_days_of_week += str(el)

                    if interval not in new_result:
                        new_result[interval] = []

                    new_result[interval].append({
                        'fromDate': dates[0],
                        'toDate': dates[len(dates) - 1],
                        'daysOfWeek': str_days_of_week,
                        'total': len(dates)
                    })

        new_results = []
        for interval, dates in new_result.items():
            splitstr = interval.split("-")
            splitstrdep = splitstr[0].split(":")
            splitstrarr = splitstr[1].split(":")

            for d in dates:
                new_results.append({
                    'deptime': f'{splitstrdep[0]}{splitstrdep[1]}',
                    'arrtime': f'{splitstrarr[0]}{splitstrarr[1]}',
                    'fromDate': str(d['fromDate']),
                    'toDate': str(d['toDate']),
                    'daysOfWeek': d['daysOfWeek'],
                    'from': lookup_flight['from'],
                    'to': lookup_flight['to'],
                    'flight': lookup_flight['flight'],
                    'freight': lookup_flight['freight'],
                    'seats': lookup_flight['seats'],
                    'deltaArrDay': lookup_flight['deltaArrDay'],
                    'ACType': lookup_flight['ACType']
                })

        print('new results are: ')
        print(new_results)

        with open('flights_result_processing.json') as f:
            data = json.load(f)

        data.extend(new_results)

        with open('flights_result_processing.json', 'w') as f:
            json.dump(data, f)

        with open('flights.txt', 'a') as f:
            f.write(f"{lookup_flight['flight']}, {lookup_flight['from']}, {lookup_flight['to']}\n")