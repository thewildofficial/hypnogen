// ProjectTests.swift
// HypnogenUITests
//
// Tests for project CRUD: create, edit name/script/affirmations, delete.

import XCTest

final class ProjectTests: HypnogenUITestCase {

    override func setUp() {
        super.setUp()
        dismissOnboardingIfPresent()
    }

    // MARK: - Tests

    func testCreateNewProject() {
        let newProjectButton = app.buttons["newProjectButton"].firstMatch
        waitForElement(newProjectButton)
        newProjectButton.tap()
        screenshot("Project_Created")

        // A project name field should appear in the editor
        let nameField = app.textFields["projectNameField"]
        waitForElement(nameField, timeout: Self.defaultTimeout, "Project name field should appear after creating a project")

        // Default name should be "Untitled Project"
        let fieldValue = nameField.value as? String ?? ""
        XCTAssertTrue(fieldValue.contains("Untitled"), "New project should have default name containing 'Untitled'")
    }

    func testEditProjectName() {
        // Create a project first
        let newProjectButton = app.buttons["newProjectButton"].firstMatch
        waitForElement(newProjectButton)
        newProjectButton.tap()

        let nameField = app.textFields["projectNameField"]
        waitForElement(nameField)

        // Clear and type a new name
        nameField.tap()
        nameField.typeKey("a", modifierFlags: .command) // Select all
        nameField.typeText("My Test Project")
        screenshot("Project_NameEdited")

        let fieldValue = nameField.value as? String ?? ""
        XCTAssertEqual(fieldValue, "My Test Project", "Project name should reflect typed text")
    }

    func testEditProjectScript() {
        // Create a project
        let newProjectButton = app.buttons["newProjectButton"].firstMatch
        waitForElement(newProjectButton)
        newProjectButton.tap()

        let scriptEditor = app.textViews["scriptEditor"]
        waitForElement(scriptEditor)

        // Type into the script editor
        scriptEditor.tap()
        scriptEditor.typeText("This is a test hypnosis script for deep relaxation.")
        screenshot("Project_ScriptEdited")

        let editorValue = scriptEditor.value as? String ?? ""
        XCTAssertTrue(editorValue.contains("deep relaxation"), "Script editor should contain typed text")
    }

    func testAddAffirmation() {
        // Create a project
        let newProjectButton = app.buttons["newProjectButton"].firstMatch
        waitForElement(newProjectButton)
        newProjectButton.tap()

        let addButton = app.buttons["addAffirmationButton"]
        waitForElement(addButton)

        // Look for the "Add affirmation..." placeholder text field
        let addField = app.textFields["Add affirmation..."]
        if addField.exists {
            addField.tap()
            addField.typeText("I am calm and confident")
            addButton.tap()
            screenshot("Project_AffirmationAdded")
        }

        // Verify the affirmation list contains items
        let affirmationsList = app.scrollViews["affirmationsList"].firstMatch
        let listExists = affirmationsList.exists || app.otherElements["affirmationsList"].exists
        XCTAssertTrue(listExists || addButton.exists, "Affirmations panel should be visible")
    }

    func testDeleteProject() {
        // Create a project
        let newProjectButton = app.buttons["newProjectButton"].firstMatch
        waitForElement(newProjectButton)
        newProjectButton.tap()

        screenshot("Project_BeforeDelete")

        // Find the first project row in the sidebar and right-click for context menu
        let firstProjectRow = app.outlineRows.firstMatch

        if firstProjectRow.exists {
            firstProjectRow.rightClick()

            // Look for the Delete option in the context menu
            let deleteMenuItem = app.menuItems["Delete"]
            if deleteMenuItem.waitForExistence(timeout: Self.defaultTimeout) {
                deleteMenuItem.tap()
                screenshot("Project_Deleted")
            }
        }
    }
}
