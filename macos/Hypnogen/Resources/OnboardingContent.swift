// OnboardingContent.swift
// Hypnogen
//
// Content definitions for onboarding: feature tour pages, tips, glossary, and troubleshooting.

import Foundation

// MARK: - Feature Tour

/// A single page in the feature tour walkthrough.
struct TourPage: Identifiable {
    let id: Int
    let title: String
    let subtitle: String
    let body: String
    let sfSymbol: String
}

/// All pages in the feature tour, ordered sequentially.
enum FeatureTourContent {
    static let pages: [TourPage] = [
        TourPage(
            id: 0,
            title: "Welcome to Hypnogen",
            subtitle: "Create personalised hypnosis audio",
            body: """
            Hypnogen turns your words into soothing, layered audio sessions — \
            complete with background music, binaural beats, and natural-sounding speech.

            This quick tour shows you around the app. You can skip it at any time \
            and reopen it later from the Help menu.
            """,
            sfSymbol: "waveform.circle.fill"
        ),
        TourPage(
            id: 1,
            title: "Projects",
            subtitle: "Write and organise your sessions",
            body: """
            Each project holds a script and a set of affirmations. \
            Write what you want to hear, tweak the wording, and choose a voice that feels right.

            Projects are saved automatically so you never lose your work.
            """,
            sfSymbol: "doc.text.fill"
        ),
        TourPage(
            id: 2,
            title: "Render Queue",
            subtitle: "Watch your sessions come to life",
            body: """
            When you're happy with a project, hit Render. \
            The Render Queue shows progress for every session being generated.

            You can queue multiple projects and let them process in the background.
            """,
            sfSymbol: "list.bullet.clipboard.fill"
        ),
        TourPage(
            id: 3,
            title: "Outputs Library",
            subtitle: "Listen and share your finished audio",
            body: """
            Completed sessions appear in the Outputs Library. \
            Preview them directly, or reveal the file in Finder to share it however you like.
            """,
            sfSymbol: "music.note.list"
        ),
        TourPage(
            id: 4,
            title: "Settings",
            subtitle: "Customise your experience",
            body: """
            Choose a default voice, configure the rendering server, \
            and fine-tune how Hypnogen works for you.

            Open Settings any time with ⌘, (Command + comma).
            """,
            sfSymbol: "gearshape.fill"
        ),
    ]
}

// MARK: - Tips & Glossary

/// A helpful tip displayed as a card.
struct Tip: Identifiable {
    let id: Int
    let title: String
    let body: String
    let sfSymbol: String
}

/// A glossary entry explaining a term in plain language.
struct GlossaryEntry: Identifiable {
    let id: Int
    let term: String
    let definition: String
}

enum TipsContent {
    static let tips: [Tip] = [
        Tip(
            id: 0,
            title: "Pick the right voice",
            body: """
            Each voice has its own character. Try a few to find one \
            that feels calming and natural to you.
            """,
            sfSymbol: "person.wave.2"
        ),
        Tip(
            id: 1,
            title: "Use a seed for consistency",
            body: """
            Setting a seed number means the same project will produce \
            the same audio every time — helpful when you want predictable results.
            """,
            sfSymbol: "number.circle"
        ),
        Tip(
            id: 2,
            title: "Keep affirmations short",
            body: """
            Short, positive statements work best. \
            "I am calm and focused" is more effective than a long paragraph.
            """,
            sfSymbol: "text.quote"
        ),
        Tip(
            id: 3,
            title: "Export stems for editing",
            body: """
            Enable "Export Stems" in project settings to get separate files \
            for voice, music, and tones — perfect for mixing in another app.
            """,
            sfSymbol: "slider.horizontal.3"
        ),
    ]
}

enum GlossaryContent {
    static let entries: [GlossaryEntry] = [
        GlossaryEntry(
            id: 0,
            term: "Shepherd Track",
            definition: """
            The main spoken voice that guides you through the session. \
            It reads your script aloud in a calm, natural tone.
            """
        ),
        GlossaryEntry(
            id: 1,
            term: "Swarm Track",
            definition: """
            Soft, layered whispers of your affirmations that play underneath \
            the main voice, reinforcing the message at a subconscious level.
            """
        ),
        GlossaryEntry(
            id: 2,
            term: "Binaural Beats",
            definition: """
            Subtle tones played at slightly different frequencies in each ear. \
            They can help promote relaxation or focus — just wear headphones.
            """
        ),
        GlossaryEntry(
            id: 3,
            term: "Seed",
            definition: """
            A number that controls randomness. The same seed with the same \
            settings produces identical audio, so you can recreate a session exactly.
            """
        ),
        GlossaryEntry(
            id: 4,
            term: "Stems",
            definition: """
            The individual audio layers (voice, music, tones) that make up \
            a session. Exporting stems lets you remix them in another app.
            """
        ),
        GlossaryEntry(
            id: 5,
            term: "Render",
            definition: """
            The process of generating your finished audio file from a project. \
            It combines the script, affirmations, voice, and audio layers.
            """
        ),
    ]
}

// MARK: - Troubleshooting

/// A troubleshooting entry with problem, cause, and solution.
struct TroubleshootingEntry: Identifiable {
    let id: Int
    let problem: String
    let cause: String
    let solution: String
    let sfSymbol: String
}

enum TroubleshootingContent {
    static let entries: [TroubleshootingEntry] = [
        TroubleshootingEntry(
            id: 0,
            problem: "Render stuck or not starting",
            cause: "The rendering worker might not be running, or the connection settings may be wrong.",
            solution: """
            Open Settings → Worker and check the host and port. \
            Make sure the Hypnogen worker process is running in your terminal.
            """,
            sfSymbol: "exclamationmark.arrow.circlepath"
        ),
        TroubleshootingEntry(
            id: 1,
            problem: "Audio sounds robotic or glitchy",
            cause: "The voice model may still be downloading, or the system ran out of memory.",
            solution: """
            Wait for the model to finish downloading (first render takes longer). \
            Close other heavy apps to free up memory and try again.
            """,
            sfSymbol: "waveform.badge.exclamationmark"
        ),
        TroubleshootingEntry(
            id: 2,
            problem: "Model downloading slowly",
            cause: "Large voice models need to be fetched the first time they are used.",
            solution: """
            This is normal for the first render with a new voice. \
            The model is cached locally so future renders will be much faster.
            """,
            sfSymbol: "arrow.down.circle"
        ),
        TroubleshootingEntry(
            id: 3,
            problem: "Disk space warning",
            cause: "Rendered audio and cached models take up storage over time.",
            solution: """
            Delete old outputs from the Library, or remove unused voice models \
            from ~/Library/Application Support/Hypnogen/models.
            """,
            sfSymbol: "externaldrive.badge.exclamationmark"
        ),
        TroubleshootingEntry(
            id: 4,
            problem: "App feels unresponsive",
            cause: "A large project or many queued renders can slow things down.",
            solution: """
            Try reducing the number of simultaneous renders. \
            If the problem persists, restart the app with ⌘Q and reopen.
            """,
            sfSymbol: "tortoise"
        ),
    ]
}
