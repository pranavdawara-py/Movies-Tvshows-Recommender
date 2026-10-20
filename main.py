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

    # year overlap: movie was active at any point inside the user's window
    if min_year is not None:
        result = result[result['end_year'] >= min_year]
    if max_year is not None:
        result = result[result['start_year'] <= max_year]

    # duration range in minutes
    if min_duration is not None:
        result = result[result['duration_min'] >= min_duration]
    if max_duration is not None:
        result = result[result['duration_min'] <= max_duration]

    # rating range
    if min_rating is not None:
        result = result[result['rating'] >= min_rating]
    if max_rating is not None:
        result = result[result['rating'] <= max_rating]

    # certificate: movie passes if its certificate is in the selected list
    if certificates:
        result = result[result['certificate'].isin(certificates)]

    # genre DNF: each group is AND, groups are OR
    # e.g. [['Horror', 'Comedy'], ['Action']] means (Horror AND Comedy) OR (Action)
    if genre_groups:
        def matches_genre(movie_genres, groups):
            movie_genre_list = [g.strip().lower() for g in movie_genres.split(',')]
            for group in groups:
                required = [g.strip().lower() for g in group]
                if all(r in movie_genre_list for r in required):
                    return True
            return False

        result = result[result['genre'].apply(lambda g: matches_genre(g, genre_groups))]

    # stars include: same DNF logic as genre
    if star_include_groups:
        def matches_stars_include(movie_stars, groups):
            movie_star_list = [s.strip().lower() for s in movie_stars.split(',')]
            for group in groups:
                required = [s.strip().lower() for s in group]
                if all(r in movie_star_list for r in required):
                    return True
            return False

        result = result[result['stars'].apply(lambda s: matches_stars_include(s, star_include_groups))]

    # stars exclude: reject movie if it has any excluded star
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
