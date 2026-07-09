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
from pathlib import Path

import pandas as pd
import streamlit as st


# ----------------------------------------------------------------------
# The Munros (loaded from munros.csv, so the map and stats appear with no upload)
# ----------------------------------------------------------------------
# munros.csv holds all 282 current Munros, with name, latitude, longitude and
# summit height, derived from the Database of British and Irish Hills (DoBIH),
# v8.0.1. Keep munros.csv in the same folder as this script (and in the GitHub
# repo when you deploy).
#
# Note on the "typical route" figures: distance and ascent depend on which
# route you take up a hill, so there is no single authoritative value per Munro.
# This version therefore shows only the summit height in the quiet stats line.

_munros_df = pd.read_csv(Path(__file__).parent / "munros.csv")
MUNROS = _munros_df.to_dict("records")
# Some Munros share a name (there are two Ben More's, three An Socach's, and so
# on), so the dropdown and lookup use a unique "display_name" that adds a rough
# area and the height. The plain "name" is what gets stored in the reflection.
MUNRO_BY_NAME = {m["display_name"]: m for m in MUNROS}
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
    st.header("Record a Munro")
    st.write("Choose a Munro you've climbed. It can be a "
             "recent one or one from years ago.")

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
    st.caption(f"For the record: {hill['height_m']} m summit.")

    if st.button("Save this round"):
        if not date:
            st.warning("Add the date first.")
        elif not any(answers.values()):
            st.warning("Write at least one reflection before saving.")
        else:
            get_entries().append({
                "hill": hill["name"],          # the plain name, for display
                "lat": hill["lat"],            # coordinates captured now, so
                "lon": hill["lon"],            # revisiting needs no re-lookup
                "height_m": hill["height_m"],
                "date": date.isoformat(),
                "notes": [],
                **answers,
            })
            st.success("Saved for this session. See it under 'My rounds', or go "
                       "to 'Finish' when you're done.")


def page_my_rounds():
    st.header("My munros")
    entries = get_entries()
    if not entries:
        st.write("No rounds recorded yet this session. Go to 'Record a round' to start.")
        return

    labels = [f"{e['hill']} ({e['date']})" for e in entries]
    i = labels.index(st.selectbox("Choose a round to revisit", labels))
    entry = entries[i]

    st.subheader(entry["hill"])
    st.caption(entry["date"])
    st.map(pd.DataFrame({"lat": [entry["lat"]], "lon": [entry["lon"]]}), zoom=9)

    for key, question in PROMPTS:
        if entry.get(key):
            st.markdown(f"**{question}**")
            st.write(entry[key])

    st.caption(f"For the record: {entry['height_m']} m summit.")

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
