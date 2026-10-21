import streamlit as st
import html
from main import load_data, filter_movies, smart_filter


@st.cache_data
def get_data():
    return load_data()

df_full = get_data()


def init_state():
    if 'certificates' not in st.session_state:
        st.session_state.certificates = []
    if 'genre_groups' not in st.session_state:
        st.session_state.genre_groups = []
    if 'star_include_groups' not in st.session_state:
        st.session_state.star_include_groups = []
    if 'star_exclude' not in st.session_state:
        st.session_state.star_exclude = []
    if 'results' not in st.session_state:
        st.session_state.results = None
    # filters used in the last Suggest click, needed by smart_filter
    if 'last_filters' not in st.session_state:
        st.session_state.last_filters = None
    # results from the last Suggest click, needed by smart_filter
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    # bumped by Clear All so that text inputs (which use this in their key) reset
    if 'clear_count' not in st.session_state:
        st.session_state.clear_count = 0

init_state()

# read once so all widget keys in this run are consistent
clear_count = st.session_state.clear_count


def parse_int(s):
    try:
        return int(s.strip())
    except:
        return None

def parse_float(s):
    try:
        return float(s.strip())
    except:
        return None


st.title("Movies & TV Shows Recommender")

st.write("### Filters")

year_col, dur_col, rating_col = st.columns(3)

with year_col:
    st.write("**Year**")
    y1, y2 = st.columns(2)
    with y1:
        min_year_str = st.text_input("Min", key=f"min_year_{clear_count}", placeholder="e.g. 2000")
    with y2:
        max_year_str = st.text_input("Max", key=f"max_year_{clear_count}", placeholder="e.g. 2024")

with dur_col:
    st.write("**Duration (minutes)**")
    d1, d2 = st.columns(2)
    with d1:
        min_dur_str = st.text_input("Min", key=f"min_dur_{clear_count}", placeholder="e.g. 60")
    with d2:
        max_dur_str = st.text_input("Max", key=f"max_dur_{clear_count}", placeholder="e.g. 180")

with rating_col:
    st.write("**Rating**")
    r1, r2 = st.columns(2)
    with r1:
        min_rating_str = st.text_input("Min", key=f"min_rating_{clear_count}", placeholder="e.g. 7.0")
    with r2:
        max_rating_str = st.text_input("Max", key=f"max_rating_{clear_count}", placeholder="e.g. 10.0")

st.markdown("---")

cert_col, genre_col, inc_col, exc_col = st.columns(4)

with cert_col:
    st.write("**Certificate**")
    st.caption("any match passes")
    cert_inp = st.text_input("e.g. PG-13, R", key=f"cert_inp_{clear_count}")
    add_btn, del_btn, clr_btn = st.columns(3)
    with add_btn:
        if st.button("Add", key="cert_add"):
            items = [x.strip() for x in cert_inp.split(',') if x.strip()]
            st.session_state.certificates.extend(items)
    with del_btn:
        if st.button("Del Last", key="cert_del"):
            if st.session_state.certificates:
                st.session_state.certificates.pop()
    with clr_btn:
        if st.button("Clear", key="cert_clr"):
            st.session_state.certificates = []
    for c in st.session_state.certificates:
        st.write(f"• {c}")

with genre_col:
    st.write("**Genre**")
    st.caption("comma = AND within entry, entries = OR")
    genre_inp = st.text_input("e.g. Horror, Comedy", key=f"genre_inp_{clear_count}")
    add_btn, del_btn, clr_btn = st.columns(3)
    with add_btn:
        if st.button("Add", key="genre_add"):
            if genre_inp.strip():
                group = [x.strip() for x in genre_inp.split(',') if x.strip()]
                st.session_state.genre_groups.append(group)
    with del_btn:
        if st.button("Del Last", key="genre_del"):
            if st.session_state.genre_groups:
                st.session_state.genre_groups.pop()
    with clr_btn:
        if st.button("Clear", key="genre_clr"):
            st.session_state.genre_groups = []
    for g in st.session_state.genre_groups:
        st.write(f"• {', '.join(g)}")

with inc_col:
    st.write("**Stars Include**")
    st.caption("comma = AND within entry, entries = OR")
    inc_inp = st.text_input("e.g. Tom Hanks", key=f"inc_inp_{clear_count}")
    add_btn, del_btn, clr_btn = st.columns(3)
    with add_btn:
        if st.button("Add", key="inc_add"):
            if inc_inp.strip():
                group = [x.strip() for x in inc_inp.split(',') if x.strip()]
                st.session_state.star_include_groups.append(group)
    with del_btn:
        if st.button("Del Last", key="inc_del"):
            if st.session_state.star_include_groups:
                st.session_state.star_include_groups.pop()
    with clr_btn:
        if st.button("Clear", key="inc_clr"):
            st.session_state.star_include_groups = []
    for g in st.session_state.star_include_groups:
        st.write(f"• {', '.join(g)}")

with exc_col:
    st.write("**Stars Exclude**")
    st.caption("any listed star → title excluded")
    exc_inp = st.text_input("e.g. Adam Sandler", key=f"exc_inp_{clear_count}")
    add_btn, del_btn, clr_btn = st.columns(3)
    with add_btn:
        if st.button("Add", key="exc_add"):
            items = [x.strip() for x in exc_inp.split(',') if x.strip()]
            st.session_state.star_exclude.extend(items)
    with del_btn:
        if st.button("Del Last", key="exc_del"):
            if st.session_state.star_exclude:
                st.session_state.star_exclude.pop()
    with clr_btn:
        if st.button("Clear", key="exc_clr"):
            st.session_state.star_exclude = []
    for s in st.session_state.star_exclude:
        st.write(f"• {s}")

st.markdown("---")

clear_all_col, suggest_col, _ = st.columns([1, 2, 1])
with clear_all_col:
    if st.button("Clear All Filters"):
        st.session_state.certificates = []
        st.session_state.genre_groups = []
        st.session_state.star_include_groups = []
        st.session_state.star_exclude = []
        st.session_state.clear_count += 1
        st.rerun()
with suggest_col:
    suggest_clicked = st.button("Suggest", type="primary", use_container_width=True)

if suggest_clicked:
    new_filters = {
        'min_year':           parse_int(min_year_str),
        'max_year':           parse_int(max_year_str),
        'min_duration':       parse_int(min_dur_str),
        'max_duration':       parse_int(max_dur_str),
        'min_rating':         parse_float(min_rating_str),
        'max_rating':         parse_float(max_rating_str),
        'certificates':       st.session_state.certificates or None,
        'genre_groups':       st.session_state.genre_groups or None,
        'star_include_groups': st.session_state.star_include_groups or None,
        'star_exclude':       st.session_state.star_exclude or None,
    }

    if st.session_state.last_filters is not None:
        result = smart_filter(df_full, st.session_state.last_result, st.session_state.last_filters, new_filters)
    else:
        result = filter_movies(df_full, **new_filters)

    st.session_state.results = result
    st.session_state.last_filters = new_filters
    st.session_state.last_result = result

if st.session_state.results is not None:
    results = st.session_state.results
    st.write(f"### Found {len(results)} titles")

    if len(results) == 0:
        st.info("No titles match your filters. Try relaxing some criteria.")
    else:
        cards_html = '<div style="display:flex; overflow-x:auto; gap:16px; padding:12px 0">'
        for _, row in results.iterrows():
            year = str(row['start_year']) if row['start_year'] == row['end_year'] else f"{row['start_year']}–{row['end_year']}"
            title = html.escape(str(row['title']))
            genre = html.escape(str(row['genre']))
            stars = html.escape(str(row['stars']))
            desc  = html.escape(str(row['description']))
            if len(desc) > 220:
                desc = desc[:220] + "..."
            cards_html += f'''
            <div style="min-width:260px;max-width:260px;border:1px solid #ddd;border-radius:8px;
                        padding:14px;background:#fafafa;flex-shrink:0;font-family:sans-serif">
                <div style="font-weight:bold;font-size:15px;margin-bottom:6px">{title}</div>
                <div style="font-size:13px;color:#333">{year} &nbsp;·&nbsp; ⭐ {row['rating']} &nbsp;·&nbsp; {row['duration_min']} min</div>
                <div style="font-size:12px;color:#555;margin-top:3px">{row['certificate']} &nbsp;·&nbsp; {genre}</div>
                <div style="font-size:12px;color:#666;margin-top:3px">{stars}</div>
                <hr style="margin:8px 0;border:none;border-top:1px solid #e0e0e0">
                <div style="font-size:12px;color:#555;line-height:1.5">{desc}</div>
            </div>'''
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
