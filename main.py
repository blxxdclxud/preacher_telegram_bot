from aiogram import executor
from bot import dp, scheduler, prepare_mailing, _config

if __name__ == '__main__':
    mailing_times = _config["mailing_times"]

    # planning a mailing
    # this job will call prepare_mailing('ayah') function
    scheduler.add_job(prepare_mailing, trigger='cron', args=['ayah'], day_of_week='mon-sun',
                      hour=mailing_times["ayah"]["hour"],
                      minute=mailing_times["ayah"]["minute"],
                      end_date='2025-10-13')
    # this job will call prepare_mailing('dua') function
    scheduler.add_job(prepare_mailing, trigger='cron', args=['dua'], day_of_week='mon-sun',
                      hour=mailing_times["dua"]["hour"],
                      minute=mailing_times["dua"]["minute"],
                      end_date='2025-10-13')
    # this job will call prepare_mailing('hadith') function
    scheduler.add_job(prepare_mailing, trigger='cron', args=['hadith'], day_of_week='mon-sun',
                      hour=mailing_times["hadith"]["hour"],
                      minute=mailing_times["hadith"]["minute"],
                      end_date='2025-10-13')

    scheduler.start()
    executor.start_polling(dp, skip_updates=True)

