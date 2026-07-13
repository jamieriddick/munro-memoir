"""
Munro Memoir
A small web app for recording and reflecting on days in the Scottish hills.
"""

import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# ----------------------------------------------------------------------
# The Munros (loaded from munros.csv, so the map and stats appear with no upload)
# munros.csv holds all 282 current Munros, with name, latitude, longitude and
# summit height, derived from the Database of British and Irish Hills (DoBIH),
# Shows the summit height in the quiet stats line.

_munros_df = pd.read_csv(Path(__file__).parent / "munros_all_282.csv")
MUNROS = _munros_df.to_dict("records")
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
# st.session_state is Streamlit's per-session memory. I keep the entries a
# participant makes here, so they can revisit them while the app is open. It is
# not saved anywhere and is gone when they close the tab:
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

    # The summit heightt.
    st.caption(f"For the record: {hill['height_m']} m summit.")

    if st.button("Save this round"):
        if not date:
            st.warning("Add the date first.")
        elif not any(answers.values()):
            st.warning("Write at least one reflection before saving.")
        else:
            get_entries().append({
                "hill": hill["name"],          # the plain name, for display
                "lat": hill["lat"],            
                "lon": hill["lon"],            
                "height_m": hill["height_m"],
                "date": date.isoformat(),
                "notes": [],
                **answers,
            })
            st.success("Saved for this session. See it under 'My munros' (arrows in top-left if you're using a phone), or go "
                       "to 'Finish' when you're done.")


def page_my_rounds():
    st.header("My munros")
    entries = get_entries()
    if not entries:
        st.write("No munros recorded yet this session. Go to 'Record a munro' to start.")
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
        st.write("Record at least one munro first, then come back here.")
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

    page = st.sidebar.radio("Go to", ["Record a round", "My munros", "Finish"])
    if page == "Record a round":
        page_record()
    elif page == "My munros":
        page_my_rounds()
    else:
        page_finish()


if __name__ == "__main__":
    main()

