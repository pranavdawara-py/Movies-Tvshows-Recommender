import pandas as pd

def load_data():
    df = pd.read_csv('data_clean.csv')
    return df


def filter_movies(df, min_year=None, max_year=None,
                  min_duration=None, max_duration=None,
                  min_rating=None, max_rating=None,
                  certificates=None,
                  genre_groups=None,
                  star_include_groups=None, star_exclude=None):

    result = df.copy()

    # FILTERING based on YEAR
    if min_year is not None:
        result = result[result['end_year'] >= min_year]
    if max_year is not None:
        result = result[result['start_year'] <= max_year]

    # FILTERING based on DURATION
    if min_duration is not None:
        result = result[result['duration_min'] >= min_duration]
    if max_duration is not None:
        result = result[result['duration_min'] <= max_duration]

    # FILTERING based on RATING
    if min_rating is not None:
        result = result[result['rating'] >= min_rating]
    if max_rating is not None:
        result = result[result['rating'] <= max_rating]

    # FILTERING based on CERTIFICATE
    if certificates:
        result = result[result['certificate'].isin(certificates)]

    # FILTERING based on GENRE
    if genre_groups:
        def matches_genre(movie_genres, groups):
            movie_genre_list = [g.strip().lower() for g in movie_genres.split(',')]
            for group in groups:
                required = [g.strip().lower() for g in group]
                if all(r in movie_genre_list for r in required):
                    return True
            return False

        result = result[result['genre'].apply(lambda g: matches_genre(g, genre_groups))]

    # Filtering based on STARS include
    if star_include_groups:
        def matches_stars_include(movie_stars, groups):
            movie_star_list = [s.strip().lower() for s in movie_stars.split(',')]
            for group in groups:
                required = [s.strip().lower() for s in group]
                if all(r in movie_star_list for r in required):
                    return True
            return False

        result = result[result['stars'].apply(lambda s: matches_stars_include(s, star_include_groups))]

    # FILTERING based on STARS exclude
    if star_exclude:
        exclude_lower = [s.strip().lower() for s in star_exclude]

        def has_excluded_star(movie_stars):
            movie_star_list = [s.strip().lower() for s in movie_stars.split(',')]
            return any(s in movie_star_list for s in exclude_lower)

        result = result[~result['stars'].apply(has_excluded_star)]

    return result.reset_index(drop=True)


def show_results(result):
    print(f"\nFound {len(result)} titles\n")
    for _, row in result.iterrows():
        year = str(row['start_year']) if row['start_year'] == row['end_year'] else f"{row['start_year']}-{row['end_year']}"
        print(f"{row['title']} ({year})")
        print(f"  Rating: {row['rating']}  |  {row['duration_min']} min  |  {row['certificate']}")
        print(f"  Genre: {row['genre']}")
        print(f"  Stars: {row['stars']}")
        print(f"  {row['description']}")
        print()


# Specific filter functions which will be used for incremental filtering

def filter_year(df, min_year, max_year):
    result = df
    if min_year is not None:
        result = result[result['end_year'] >= min_year]
    if max_year is not None:
        result = result[result['start_year'] <= max_year]
    return result

def filter_duration(df, min_duration, max_duration):
    result = df
    if min_duration is not None:
        result = result[result['duration_min'] >= min_duration]
    if max_duration is not None:
        result = result[result['duration_min'] <= max_duration]
    return result

def filter_rating(df, min_rating, max_rating):
    result = df
    if min_rating is not None:
        result = result[result['rating'] >= min_rating]
    if max_rating is not None:
        result = result[result['rating'] <= max_rating]
    return result

def filter_certificate(df, certificates):
    if certificates:
        return df[df['certificate'].isin(certificates)]
    return df

def filter_genre(df, genre_groups):
    if not genre_groups:
        return df
    def matches(movie_genres):
        movie_list = [g.strip().lower() for g in movie_genres.split(',')]
        for group in genre_groups:
            required = [g.strip().lower() for g in group]
            if all(r in movie_list for r in required):
                return True
        return False
    return df[df['genre'].apply(matches)]

def filter_stars(df, include_groups, exclude_stars):
    result = df
    if include_groups:
        def matches_include(movie_stars):
            star_list = [s.strip().lower() for s in movie_stars.split(',')]
            for group in include_groups:
                required = [s.strip().lower() for s in group]
                if all(r in star_list for r in required):
                    return True
            return False
        result = result[result['stars'].apply(matches_include)]
    if exclude_stars:
        exclude_lower = [s.strip().lower() for s in exclude_stars]
        def has_excluded(movie_stars):
            star_list = [s.strip().lower() for s in movie_stars.split(',')]
            return any(s in star_list for s in exclude_lower)
        result = result[~result['stars'].apply(has_excluded)]
    return result


# if all filters got stricter since last Suggest, we can just narrow down the existing result
# instead of scanning the full dataset again; if any filter got looser, we have to rescan all
def smart_filter(df_full, current_result, old_f, new_f):

    needs_rerun = False
    apply_year = apply_duration = apply_rating = False
    apply_cert = apply_genre = apply_stars = False

    # year: min going up is stricter, min going down or removed is looser
    if new_f.get('min_year') != old_f.get('min_year') or new_f.get('max_year') != old_f.get('max_year'):
        apply_year = True
        old_min, new_min = old_f.get('min_year'), new_f.get('min_year')
        old_max, new_max = old_f.get('max_year'), new_f.get('max_year')
        if (old_min is not None) and (new_min is None or new_min < old_min):
            needs_rerun = True
        if (old_max is not None) and (new_max is None or new_max > old_max):
            needs_rerun = True

    # duration: same logic as year
    if new_f.get('min_duration') != old_f.get('min_duration') or new_f.get('max_duration') != old_f.get('max_duration'):
        apply_duration = True
        old_min, new_min = old_f.get('min_duration'), new_f.get('min_duration')
        old_max, new_max = old_f.get('max_duration'), new_f.get('max_duration')
        if (old_min is not None) and (new_min is None or new_min < old_min):
            needs_rerun = True
        if (old_max is not None) and (new_max is None or new_max > old_max):
            needs_rerun = True

    # rating: same logic as year
    if new_f.get('min_rating') != old_f.get('min_rating') or new_f.get('max_rating') != old_f.get('max_rating'):
        apply_rating = True
        old_min, new_min = old_f.get('min_rating'), new_f.get('min_rating')
        old_max, new_max = old_f.get('max_rating'), new_f.get('max_rating')
        if (old_min is not None) and (new_min is None or new_min < old_min):
            needs_rerun = True
        if (old_max is not None) and (new_max is None or new_max > old_max):
            needs_rerun = True

    # certificate: fewer allowed certs = stricter; gaining a new cert option = looser
    if new_f.get('certificates') != old_f.get('certificates'):
        apply_cert = True
        old_set = set(old_f.get('certificates') or [])
        new_set = set(new_f.get('certificates') or [])
        if not new_set.issubset(old_set):  # new set has certs that weren't allowed before
            needs_rerun = True

    # genre: fewer OR groups = stricter (harder to satisfy); more groups = looser
    if new_f.get('genre_groups') != old_f.get('genre_groups'):
        apply_genre = True
        old_len = len(old_f.get('genre_groups') or [])
        new_len = len(new_f.get('genre_groups') or [])
        if new_len > old_len:
            needs_rerun = True

    # stars: more include groups = more OR paths = looser; fewer exclude = looser
    if new_f.get('star_include_groups') != old_f.get('star_include_groups') or new_f.get('star_exclude') != old_f.get('star_exclude'):
        apply_stars = True
        old_inc = len(old_f.get('star_include_groups') or [])
        new_inc = len(new_f.get('star_include_groups') or [])
        old_exc = len(old_f.get('star_exclude') or [])
        new_exc = len(new_f.get('star_exclude') or [])
        if new_inc > old_inc or new_exc < old_exc:
            needs_rerun = True

    if needs_rerun:
        return filter_movies(df_full, **new_f)

    # all changes are stricter, apply only the changed filter functions on current_result
    result = current_result
    if apply_year:
        result = filter_year(result, new_f.get('min_year'), new_f.get('max_year'))
    if apply_duration:
        result = filter_duration(result, new_f.get('min_duration'), new_f.get('max_duration'))
    if apply_rating:
        result = filter_rating(result, new_f.get('min_rating'), new_f.get('max_rating'))
    if apply_cert:
        result = filter_certificate(result, new_f.get('certificates'))
    if apply_genre:
        result = filter_genre(result, new_f.get('genre_groups'))
    if apply_stars:
        result = filter_stars(result, new_f.get('star_include_groups'), new_f.get('star_exclude'))

    return result.reset_index(drop=True)


'''
if __name__ == '__main__':
    df = load_data()
    print(f"Loaded {len(df)} titles")

    # test 1: action movies rated 8+ from 2015 onwards
    res = filter_movies(df,
                        min_year=2015,
                        min_rating=8.0,
                        genre_groups=[['Action']])
    show_results(res.head(5))

    # test 2: horror comedy combo OR thriller, certificate PG-13 or R
    res2 = filter_movies(df,
                         genre_groups=[['Horror', 'Comedy'], ['Thriller']],
                         certificates=['PG-13', 'R'])
    show_results(res2.head(5))
'''