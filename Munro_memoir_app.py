"""
Munro Memoir
A small web app for recording and reflecting on days in the Scottish hills.

Built with Streamlit, so it is pure Python. Run it locally with:
    streamlit run munro_memoir.py

The idea is memory rather than performance. Each entry is a remembered day: a
hill, a written reflection in answer to a few prompts, and an optional photo to
jog the memory. The numbers are kept deliberately quiet. An entry can be
returned to within the session, so a memory can be added to as it comes to mind.

The app stores nothing. Reflections live only in the browser for the current
session. When the participant has finished, the app gathers up what they wrote
into one block to copy, and sends them to the study questionnaire (in the
University's Qualtrics) where they paste it in. All data is held in Qualtrics,
so the app keeps no participant data of its own.
"""

import datetime

import pandas as pd
import streamlit as st


# ----------------------------------------------------------------------
# The Munros (built into the app, so the map and stats appear with no upload)
# ----------------------------------------------------------------------
# A short sample so the app runs as-is. For the study, replace this with the
# full set of 282 from the Database of British and Irish Hills (DoBIH). The
# coordinates and route figures below are approximate placeholders.
MUNROS = [
    {"name": "Ben Nevis",              "lat": 56.7969, "lon": -5.0036, "height_m": 1345, "route_km": 17, "ascent_m": 1350},
    {"name": "Ben Macdui",             "lat": 57.0703, "lon": -3.6691, "height_m": 1309, "route_km": 18, "ascent_m": 900},
    {"name": "Braeriach",              "lat": 57.0782, "lon": -3.7289, "height_m": 1296, "route_km": 23, "ascent_m": 1100},
    {"name": "Cairn Gorm",             "lat": 57.1167, "lon": -3.6433, "height_m": 1245, "route_km": 11, "ascent_m": 700},
    {"name": "Aonach Beag",            "lat": 56.8018, "lon": -4.9614, "height_m": 1234, "route_km": 17, "ascent_m": 1300},
    {"name": "Ben Lawers",             "lat": 56.5453, "lon": -4.2206, "height_m": 1214, "route_km": 12, "ascent_m": 950},
    {"name": "Ben More (Crianlarich)", "lat": 56.3870, "lon": -4.5400, "height_m": 1174, "route_km": 11, "ascent_m": 1050},
    {"name": "Lochnagar",              "lat": 56.9558, "lon": -3.2456, "height_m": 1156, "route_km": 20, "ascent_m": 900},
    {"name": "Bidean nam Bian",        "lat": 56.6428, "lon": -5.0244, "height_m": 1150, "route_km": 11, "ascent_m": 1150},
    {"name": "Ben Cruachan",           "lat": 56.4269, "lon": -5.1283, "height_m": 1126, "route_km": 14, "ascent_m": 1250},
    {"name": "Schiehallion",           "lat": 56.6674, "lon": -4.0989, "height_m": 1083, "route_km": 10, "ascent_m": 760},
    {"name": "An Teallach",            "lat": 57.7747, "lon": -5.2722, "height_m": 1062, "route_km": 18, "ascent_m": 1450},
    {"name": "Liathach",               "lat": 57.5550, "lon": -5.4550, "height_m": 1055, "route_km": 12, "ascent_m": 1300},
    {"name": "Ben Wyvis",              "lat": 57.6850, "lon": -4.5867, "height_m": 1046, "route_km": 14, "ascent_m": 900},
    {"name": "Buachaille Etive Mor",   "lat": 56.6433, "lon": -4.9039, "height_m": 1022, "route_km": 9,  "ascent_m": 950},
    {"name": "Ben Lomond",             "lat": 56.1906, "lon": -4.6331, "height_m": 974,  "route_km": 12, "ascent_m": 970},
]
MUNRO_BY_NAME = {m["name"]: m for m in MUNROS}
MUNRO_NAMES = sorted(MUNRO_BY_NAME)


# The four reflective prompts. Each is (key, question).
PROMPTS = [
    ("companions", "Who were you with? (Please use a description rather than a real name, for example 'my sister' or 'an old school friend'.)"),
    ("moment", "A moment that stuck with you"),
    ("unseen", "Something the photos can't capture"),
    ("future", "What you'll want to remember about this day in a year"),
]


# ----------------------------------------------------------------------
# The session store (entries kept in the browser for this session only)
# ----------------------------------------------------------------------
# st.session_state is Streamlit's per-session memory. We keep the entries a
# participant makes here, so they can revisit them while the app is open. It is
# not saved anywhere and is gone when they close the tab, which is what we want:
# the only lasting copy is the one they paste into the questionnaire.

def get_entries():
    return st.session_state.setdefault("entries", [])


def assemble_text(entries):
    """Gather every entry this session into one block of plain text, ready for
    the participant to copy and paste into the questionnaire."""
    blocks = []
    for e in entries:
        lines = [f"Hill: {e['hill']} ({e['date']})"]
        for key, question in PROMPTS:
            if e.get(key):
                lines.append(f"{question}: {e[key]}")
        for note in e.get("notes", []):
            lines.append(f"Coming back to this: {note}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------

def page_record():
    st.header("Record a round")
    st.write("Choose a hill you've climbed and tell its story. It can be a "
             "recent day or one from years ago.")

    hill_name = st.selectbox("Which hill?", MUNRO_NAMES, index=None,
                             placeholder="Start typing to find a Munro")
    if not hill_name:
        return
    hill = MUNRO_BY_NAME[hill_name]

    date = st.date_input("When did you climb it?", value=None,
                         min_value=datetime.date(1950, 1, 1),
                         max_value=datetime.date.today())

    # A simple map of where the hill is: the memory is anchored to a place.
    st.map(pd.DataFrame({"lat": [hill["lat"]], "lon": [hill["lon"]]}), zoom=9)

    # The reflection leads.
    st.subheader("Looking back on the day")
    st.caption("Answer as many or as few as you like.")
    answers = {key: st.text_area(question, key=f"r_{key}", height=80)
               for key, question in PROMPTS}

    # A photo as a memory cue: shown here, never saved.
    for photo in st.file_uploader("Add a photo (not saved)",
                                  type=["jpg", "jpeg", "png"],
                                  accept_multiple_files=True) or []:
        st.image(photo)

    # The numbers, kept quiet.
    st.caption(f"For the record: {hill['height_m']} m summit; a typical route "
               f"is about {hill['route_km']} km and {hill['ascent_m']} m of ascent.")

    if st.button("Save this round"):
        if not date:
            st.warning("Add the date first.")
        elif not any(answers.values()):
            st.warning("Write at least one reflection before saving.")
        else:
            get_entries().append({
                "hill": hill_name,
                "date": date.isoformat(),
                "notes": [],
                **answers,
            })
            st.success("Saved for this session. See it under 'My rounds', or go "
                       "to 'Finish' when you're done.")


def page_my_rounds():
    st.header("My rounds")
    entries = get_entries()
    if not entries:
        st.write("No rounds recorded yet this session. Go to 'Record a round' to start.")
        return

    labels = [f"{e['hill']} ({e['date']})" for e in entries]
    i = labels.index(st.selectbox("Choose a round to revisit", labels))
    entry = entries[i]
    hill = MUNRO_BY_NAME.get(entry["hill"])

    st.subheader(entry["hill"])
    st.caption(entry["date"])
    if hill:
        st.map(pd.DataFrame({"lat": [hill["lat"]], "lon": [hill["lon"]]}), zoom=9)

    for key, question in PROMPTS:
        if entry.get(key):
            st.markdown(f"**{question}**")
            st.write(entry[key])

    if hill:
        st.caption(f"For the record: {hill['height_m']} m summit; a typical route "
                   f"is about {hill['route_km']} km and {hill['ascent_m']} m of ascent.")

    # Coming back to this: notes added while the memory is fresh in mind.
    st.divider()
    st.subheader("Coming back to this")
    for note in entry["notes"]:
        st.write(note)
    if not entry["notes"]:
        st.caption("Nothing added yet. Revisit this day whenever it comes to mind.")

    later = st.text_area("Add a note, looking back",
                         key=f"n_{i}", placeholder="How does this day feel now?",
                         height=90)
    if st.button("Add this note"):
        if later.strip():
            entry["notes"].append(later.strip())
            st.rerun()
        else:
            st.warning("Write something first.")


def page_finish():
    st.header("Finish")
    entries = get_entries()
    if not entries:
        st.write("Record at least one round first, then come back here.")
        return

    st.write("Almost done. Copy your reflections below, then go back to the "
             "questionnaire tab you came from and paste them in when asked. "
             "The questionnaire is where your answers are kept, so this step "
             "matters.")

    # The copy box. The small icon at its top right copies everything.
    st.code(assemble_text(entries), language=None)

    st.caption("Copy the text above (the icon in its top-right corner), then "
               "switch back to your questionnaire tab to paste it in.")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Munro Memoir", page_icon="mountain")
    st.title("Munro Memoir")
    st.sidebar.caption("Your reflections stay in your browser until you copy "
                       "them into the questionnaire. Nothing is saved here.")

    page = st.sidebar.radio("Go to", ["Record a round", "My rounds", "Finish"])
    if page == "Record a round":
        page_record()
    elif page == "My rounds":
        page_my_rounds()
    else:
        page_finish()


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------
# Deploying (much simpler now: no secrets, nothing to store)
# ----------------------------------------------------------------------
# 1. requirements.txt in the repo:
#        streamlit
#        pandas
# 2. Push this file and requirements.txt to a public GitHub repo.
# 3. At share.streamlit.io, sign in with GitHub, pick the repo and this file,
#    and deploy. You get a public app URL.
#
# The flow is survey-first: participants start in the Qualtrics questionnaire,
# read the information sheet and consent there, then are sent to this app to
# reflect (open it in a new tab), and finally return to the questionnaire tab
# to paste their reflections in. So the app does NOT need the survey link: it
# just tells people to switch back to the tab they came from. Put THIS app's
# public URL into the questionnaire (and the information sheet), and only ever
# share the questionnaire link publicly, so consent always comes first.

#pip install streamlit pandas
#python3 -m streamlit run munro_memoir.py