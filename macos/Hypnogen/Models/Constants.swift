// Constants.swift
// Hypnogen
//
// App-wide constants.

import Foundation

enum Constants {
    enum API {
        static let defaultHost = "127.0.0.1"
        static let defaultPort = 8008
        static let healthPath = "/health"
        static let renderJobsPath = "/v1/render-jobs"

        static var baseURL: URL {
            URL(string: "http://\(defaultHost):\(defaultPort)")!
        }
    }

    enum Defaults {
        static let voice = "af_heart"
        static let projectName = "Untitled Project"
    }

    enum Storage {
        static let appSupportSubdirectory = "Hypnogen"
        static let projectFileName = "project.json"
    }

    enum Accessibility {
        // Sidebar / Projects
        static let projectsList = "projectsList"
        static let newProjectButton = "newProjectButton"
        static let deleteProjectButton = "deleteProjectButton"
        static let projectRow = "projectRow"

        // Project Editor
        static let scriptEditor = "scriptEditor"
        static let affirmationsList = "affirmationsList"
        static let addAffirmationButton = "addAffirmationButton"
        static let removeAffirmationButton = "removeAffirmationButton"
        static let affirmationField = "affirmationField"
        static let voicePicker = "voicePicker"
        static let renderButton = "renderButton"
        static let projectNameField = "projectNameField"

        // Render Queue
        static let renderQueueList = "renderQueueList"
        static let renderJobRow = "renderJobRow"
        static let cancelJobButton = "cancelJobButton"
        static let jobProgressBar = "jobProgressBar"

        // Outputs Library
        static let outputsGrid = "outputsGrid"
        static let outputItem = "outputItem"
        static let playOutputButton = "playOutputButton"
        static let revealInFinderButton = "revealInFinderButton"

        // Navigation
        static let sidebar = "sidebar"
        static let sidebarProjectsSection = "sidebarProjectsSection"
        static let sidebarRenderQueueSection = "sidebarRenderQueueSection"
        static let sidebarOutputsSection = "sidebarOutputsSection"

        // Calibration
        enum Calibration {
            static let calibrationView = "calibrationView"
            static let yesButton = "yesButton"
            static let noButton = "noButton"
            static let skipCalibrationButton = "skipCalibrationButton"
            static let playButton = "playCalibrationButton"
            static let levelLabel = "calibrationLevelLabel"
            static let progressIndicator = "calibrationProgress"
            static let recalibrateButton = "recalibrateButton"
            static let doneButton = "calibrationDoneButton"
        }

        // Onboarding
        enum Onboarding {
            static let onboardingView = "onboardingView"
            static let skipButton = "skipButton"
            static let doneButton = "doneButton"
            static let nextButton = "nextButton"
            static let previousButton = "previousButton"
            static let dontShowAgainCheckbox = "dontShowAgainCheckbox"
            static let featureTourContainer = "featureTourContainer"
            static let featureTourPage = "featureTourPage"
            static let tipsGlossaryContainer = "tipsGlossaryContainer"
            static let tipCard = "tipCard"
            static let glossaryEntry = "glossaryEntry"
            static let troubleshootingContainer = "troubleshootingContainer"
            static let troubleshootingEntry = "troubleshootingEntry"
        }
    }
}
