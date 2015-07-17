# Can't use data_services.utils because of circular dependency (apparently)

from data_services.models import DimRun
from data_services.adapters.EMOD import EMOD_Adapter


def get_average_daily_value(dim_run,
                            channel_name,
                            species_name,
                            start_year=1,
                            end_year=None):
    """
    :param dim_run:
    :type dim_run: DimRun
    :param species_name:
    :param start_year:
    :param end_year:
    :return:
    """
    adapter = EMOD_Adapter(dim_run.baseline_key.user.username)
    data = adapter.fetch_data(dim_run.dimexecution_set.all()[0],
                              channel_name=channel_name,
                              channel_type=species_name)
    data = data.values()[0]

    # Start and End years start from 1, not from 0
    start_year -= 1
    if start_year < 0:
        start_year = 0
    end_year -= 1
    if end_year < 0:
        return None

    if end_year is None:
        data = data[int(start_year*365):]
    else:
        if len(data) < int(end_year*365) + 365:
            return None
        data = data[int(start_year*365):int(end_year*365) + 365]

    if len(data) == 0:
        return None

    return sum(data) / len(data)


def get_average_daily_eir(dim_run,
                          species_name,
                          start_year=1,
                          end_year=None):
    return get_average_daily_value(dim_run,
                                   channel_name="Daily EIR",
                                   species_name=species_name,
                                   start_year=start_year,
                                   end_year=end_year)


def get_average_daily_biting_rate(dim_run,
                                  species_name,
                                  start_year=1,
                                  end_year=None):
    return get_average_daily_value(dim_run,
                                   channel_name="Daily HBR",
                                   species_name=species_name,
                                   start_year=start_year,
                                   end_year=end_year)


def get_average_daily_sporozoite_rate(dim_run,
                                     species_name,
                                     start_year=1,
                                     end_year=None):
    return get_average_daily_value(dim_run,
                                   channel_name="Infectious Vectors",
                                   species_name=species_name,
                                   start_year=start_year,
                                   end_year=end_year)
