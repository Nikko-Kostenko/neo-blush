import QtQuick
import QtTest
import "../theme" as Theme

TestCase {
    id: test
    name: "NeoLogin"
    when: windowShown
    width: 1280
    height: 900
    visible: true

    property var config: ({ accentColor: "#a83f74", fontFamily: "Inter", background: Qt.resolvedUrl("../theme/assets/background.jpg"), avatar: Qt.resolvedUrl("../theme/assets/background.jpg"), avatarUser: "alice" })
    property var userModel: fakeUsers
    property var sessionModel: fakeSessions
    property var sddm: fakeGreeter
    property var keyboard: ({ capsLock: false })

    ListModel {
        id: fakeUsers
        property int lastIndex: 0
        ListElement { name: "alice"; realName: "Alice" }
        ListElement { name: "guest"; realName: "Guest" }
    }
    ListModel {
        id: fakeSessions
        property int lastIndex: 1
        ListElement { name: "Hyprland" }
        ListElement { name: "Hyprland (uwsm)" }
    }
    QtObject {
        id: fakeGreeter
        property string hostName: "my-pc"
        property bool canPowerOff: true
        property bool canReboot: true
        property bool canSuspend: true
        property int calls: 0
        property int powerCalls: 0
        property string lastUsername: ""
        property int lastSession: -1
        signal loginFailed()
        signal loginSucceeded()
        signal informationMessage(string message)
        function login(user, pass, session) {
            calls++;
            lastUsername = user;
            lastSession = session;
        }
        function suspend() { powerCalls++; }
        function reboot() { powerCalls++; }
        function powerOff() { powerCalls++; }
    }

    QtObject {
        id: fakeStatus
        property bool wifiAvailable: true
        property bool wifiEnabled: true
        property bool wifiConnected: true
        property int wifiStrength: 80
        property bool batteryAvailable: true
        property int batteryPercent: 76
        property bool batteryCharging: false
        signal changed()
    }
    Theme.Main { id: theme; anchors.fill: parent; statusProvider: fakeStatus }

    function init() {
        fakeGreeter.loginFailed();
        fakeGreeter.calls = 0;
        fakeGreeter.powerCalls = 0;
        theme.loginMessage = "";
        findChild(theme, "userSelector").currentIndex = 0;
        findChild(theme, "sessionSelector").currentIndex = 1;
        findChild(theme, "passwordField").text = "";
        theme.dismissPassword();
        fakeStatus.wifiAvailable = true;
        fakeStatus.batteryAvailable = true;
    }

    function test_nameRevealsPassword() {
        const password = findChild(theme, "passwordField");
        verify(!theme.passwordShown);
        verify(!password.visible);
        const identity = findChild(theme, "identityButton");
        mouseClick(identity, identity.width / 2, 115);
        verify(theme.passwordShown);
        tryCompare(password, "activeFocus", true);
        verify(password.visible);
        password.text = "test-password";
        keyClick(Qt.Key_Escape);
        verify(!theme.passwordShown);
        compare(password.text, "");
    }

    function test_roundAvatarAndWallpaper() {
        tryCompare(findChild(theme, "wallpaperImage"), "status", Image.Ready);
        tryCompare(findChild(theme, "avatarCanvas"), "photoLoaded", true);
        wait(30);
        const context = findChild(theme, "avatarCanvas").getContext("2d");
        compare(context.getImageData(0, 0, 1, 1).data[3], 0);
        compare(context.getImageData(41, 41, 1, 1).data[3], 255);
    }

    function test_keyboardRevealAndSubmit() {
        theme.forceActiveFocus();
        keyClick(Qt.Key_Return);
        verify(theme.passwordShown);
        const password = findChild(theme, "passwordField");
        tryCompare(password, "activeFocus", true);
        password.text = "test-password";
        keyClick(Qt.Key_Return);
        compare(fakeGreeter.calls, 1);
    }

    function test_noConfiguredPhotoUsesFallback() {
        const original = config;
        try {
            config = { background: original.background, avatar: "", avatarUser: "" };
            const canvas = findChild(theme, "avatarCanvas");
            tryCompare(canvas, "photoLoaded", false);
            compare(canvas.imageSource.toString(), "");
            verify(findChild(theme, "userName").text.length > 0);
        } finally {
            config = original;
        }
    }

    function test_statusVisibilityAndPlacement() {
        const wifi = findChild(theme, "wifiIndicator");
        const battery = findChild(theme, "batteryIndicator");
        verify(wifi.visible && battery.visible);
        fakeStatus.wifiAvailable = false;
        fakeStatus.batteryAvailable = false;
        verify(!wifi.visible && !battery.visible);
        const area = findChild(theme, "loginArea");
        verify(area.y > theme.height / 2);
        const clock = findChild(theme, "dateAndClock");
        verify(clock.y < theme.height / 3);
    }

    function test_selectedUserAndSession() {
        theme.revealPassword();
        const users = findChild(theme, "userSelector");
        const sessions = findChild(theme, "sessionSelector");
        users.currentIndex = 1;
        sessions.currentIndex = 0;
        theme.login();
        compare(fakeGreeter.lastUsername, "guest");
        compare(fakeGreeter.lastSession, 0);
        verify(theme.loggingIn);
        theme.login();
        compare(fakeGreeter.calls, 1);
    }

    function test_failureClearsPasswordAndAllowsRetry() {
        theme.revealPassword();
        const password = findChild(theme, "passwordField");
        password.text = "test-password";
        theme.login();
        fakeGreeter.loginFailed();
        verify(!theme.loggingIn);
        compare(password.text, "");
        verify(theme.loginMessage.length > 0);
        password.text = "another-test-password";
        theme.login();
        compare(fakeGreeter.calls, 2);
    }

    function test_changingUserClearsPassword() {
        theme.revealPassword();
        const password = findChild(theme, "passwordField");
        const users = findChild(theme, "userSelector");
        password.text = "test-password";
        users.currentIndex = 1;
        users.activated(1);
        compare(password.text, "");
        compare(theme.username, "guest");
    }

    function test_powerNeedsConfirmation() {
        const confirmation = findChild(theme, "powerConfirmation");
        confirmation.restart = true;
        confirmation.open();
        tryCompare(confirmation, "opened", true);
        compare(fakeGreeter.powerCalls, 0);
        findChild(theme, "cancelPower").clicked();
        tryCompare(confirmation, "opened", false);
        compare(fakeGreeter.powerCalls, 0);
        confirmation.open();
        tryCompare(confirmation, "opened", true);
        findChild(theme, "confirmPower").clicked();
        compare(fakeGreeter.powerCalls, 1);
    }

    function test_userAndSessionDropdowns() {
        theme.revealPassword();
        const users = findChild(theme, "userSelector");
        const sessions = findChild(theme, "sessionSelector");
        users.popup.open();
        tryCompare(users.popup, "opened", true);
        users.popup.close();
        sessions.popup.open();
        tryCompare(sessions.popup, "opened", true);
        sessions.popup.close();
    }
}
