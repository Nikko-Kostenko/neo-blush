#include <QQmlExtensionPlugin>
#include <qqml.h>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusObjectPath>
#include <QDBusPendingCallWatcher>
#include <QDBusPendingReply>
#include <QDir>
#include <QFile>
#include <QTimer>
#include <functional>

// Read-only system status. No network changes or elevated permissions are needed.
class DeviceStatus : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool wifiAvailable MEMBER wifiAvailable NOTIFY changed)
    Q_PROPERTY(bool wifiEnabled MEMBER wifiEnabled NOTIFY changed)
    Q_PROPERTY(bool wifiConnected MEMBER wifiConnected NOTIFY changed)
    Q_PROPERTY(int wifiStrength MEMBER wifiStrength NOTIFY changed)
    Q_PROPERTY(bool batteryAvailable MEMBER batteryAvailable NOTIFY changed)
    Q_PROPERTY(int batteryPercent MEMBER batteryPercent NOTIFY changed)
    Q_PROPERTY(bool batteryCharging MEMBER batteryCharging NOTIFY changed)
public:
    explicit DeviceStatus(QObject *parent = nullptr) : QObject(parent) {
        auto *timer = new QTimer(this);
        connect(timer, &QTimer::timeout, this, &DeviceStatus::refresh);
        timer->start(5000);
        QTimer::singleShot(0, this, &DeviceStatus::refresh);
    }
    bool wifiAvailable = false, wifiEnabled = false, wifiConnected = false;
    int wifiStrength = 0;
    bool batteryAvailable = false, batteryCharging = false;
    int batteryPercent = 0;
signals:
    void changed();
private:
    bool polling = false;
    static QString read(const QString &path) {
        QFile file(path);
        return file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()).trimmed() : QString();
    }
    void properties(const QString &path, const QString &interface,
                    std::function<void(QVariantMap)> callback) {
        auto message = QDBusMessage::createMethodCall("org.freedesktop.NetworkManager", path,
                         "org.freedesktop.DBus.Properties", "GetAll");
        message << interface;
        auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::systemBus().asyncCall(message, 2000), this);
        connect(watcher, &QDBusPendingCallWatcher::finished, this, [watcher, callback]() {
            QDBusPendingReply<QVariantMap> reply = *watcher;
            callback(reply.isError() ? QVariantMap() : reply.value());
            watcher->deleteLater();
        });
    }
    void refresh() {
        batteryAvailable = false;
        for (const QString &name : QDir("/sys/class/power_supply").entryList(QDir::Dirs | QDir::NoDotAndDotDot)) {
            const QString base = "/sys/class/power_supply/" + name + "/";
            if (read(base + "type") != "Battery" || read(base + "scope") == "Device") continue;
            bool valid = false;
            int capacity = read(base + "capacity").toInt(&valid);
            if (!valid) continue;
            batteryAvailable = true;
            batteryPercent = qBound(0, capacity, 100);
            const QString state = read(base + "status");
            batteryCharging = state == "Charging" || state == "Full";
            break;
        }
        emit changed();
        if (polling) return;
        polling = true;
        properties("/org/freedesktop/NetworkManager", "org.freedesktop.NetworkManager", [this](QVariantMap manager) {
            wifiEnabled = manager.value("WirelessEnabled").toBool();
            auto message = QDBusMessage::createMethodCall("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager",
                                  "org.freedesktop.NetworkManager", "GetDevices");
            auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::systemBus().asyncCall(message, 2000), this);
            connect(watcher, &QDBusPendingCallWatcher::finished, this, [this, watcher]() {
                QDBusPendingReply<QList<QDBusObjectPath>> reply = *watcher;
                const auto devices = reply.isError() ? QList<QDBusObjectPath>() : reply.value();
                watcher->deleteLater();
                findWifi(devices, 0);
            });
        });
    }
    void findWifi(QList<QDBusObjectPath> devices, int index) {
        if (index >= devices.size()) {
            wifiAvailable = wifiConnected = false;
            wifiStrength = 0;
            polling = false;
            emit changed();
            return;
        }
        const QString path = devices[index].path();
        properties(path, "org.freedesktop.NetworkManager.Device", [this, devices, index, path](QVariantMap device) {
            if (device.value("DeviceType").toUInt() != 2) {
                findWifi(devices, index + 1);
                return;
            }
            wifiAvailable = true;
            wifiConnected = device.value("State").toUInt() == 100;
            properties(path, "org.freedesktop.NetworkManager.Device.Wireless", [this](QVariantMap wireless) {
                const QString accessPoint = qvariant_cast<QDBusObjectPath>(wireless.value("ActiveAccessPoint")).path();
                if (!wifiConnected || accessPoint.isEmpty() || accessPoint == "/") {
                    wifiStrength = 0;
                    polling = false;
                    emit changed();
                    return;
                }
                properties(accessPoint, "org.freedesktop.NetworkManager.AccessPoint", [this](QVariantMap ap) {
                    wifiStrength = qBound(0, ap.value("Strength").toInt(), 100);
                    polling = false;
                    emit changed();
                });
            });
        });
    }
};

class NeoStatusPlugin : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char *uri) override {
        qmlRegisterType<DeviceStatus>(uri, 1, 0, "DeviceStatus");
    }
};

#include "status.moc"
