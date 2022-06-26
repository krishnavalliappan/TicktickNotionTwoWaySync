import secrets
import smtplib
import time
import datetime as dt
import pytz

from ticktick_notion_connector import TicktickNotionConnector


def send_mail(mail_id, password, error, sender_address):
    my_email = mail_id
    password = password
    connection = smtplib.SMTP("smtp.gmail.com", 587)
    connection.starttls()
    connection.login(user=my_email, password=password)
    connection.sendmail(
        from_addr=my_email,
        to_addrs=sender_address,
        msg=f"Subject: Error in Ticktick-Notion two way sync \n\n{error}"
    )
    connection.close()


def main():
    tt_no = TicktickNotionConnector()

    trial = 0
    while trial <= 50:
        sleep_time_sec = 30
        current_time = dt.datetime.now(tz=pytz.timezone('Asia/Kolkata'))
        # check if it above 10:30 PM and below 5:00 AM
        if (current_time.hour >= 22 and current_time.minute >= 30) or (
                current_time.hour <= 5 and current_time.minute < 1):
            sleep_time_sec = 1200
        try:
            tt_no.ticktick_loop_init()
            tt_no.notion_loop_init()
            tt_no.notion_check()
            tt_no.ticktick_check()
            tt_no.notion_action_project()
            tt_no.ticktick_action_project()
            tt_no.notion_action_task()
            tt_no.ticktick_action_task()
            tt_no.notion.reading_data_in_notion()
            tt_no.un_archive_check_and_action()
            tt_no.ticktick_loop_end()
            tt_no.notion_loop_end()

            trial = trial + 1
            print(trial)

            time.sleep(sleep_time_sec)

        except Exception as error:
            send_mail(secrets.mail_id, secrets.mail_password, error, secrets.sender_address)
            time.sleep(300)


if __name__ == "__main__":
    main()
