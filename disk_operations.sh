#!/bin/bash

# Arguments: disk_name, disk_label
# disk_name=$1
# disk_label=$2

non_root_users=$(awk -F: '$3 >= 1000 && $3 < 65534 {print $1}' /etc/passwd)
non_root_user_count=$(echo "$non_root_users" | wc -l)

if [ "$non_root_user_count" -eq 1 ]; then
    username=$non_root_users
    echo "Selected user: $username"
else
    echo "Available non-root users:"
    select username in $non_root_users; do
        if [ -n "$username" ]; then
            break
        else
            echo "Invalid selection. Please try again."
        fi
    done
fi

echo "输入DCP磁盘名称(例如 XX_DCP): "
read disk_label
echo "选择的磁盘设备名(例如 sda):"
read disk_name

for disk in "$disk_name"; do
    if [ -b "/dev/$disk" ]; then
        umount "/dev/$disk" 2>/dev/null

        mkfs.ext3 "/dev/$disk"

        mount_point="/run/media/$username/$disk_label"
        # mount_point=/mnt/$disk_name
        mkdir -p "$mount_point"
        mount "/dev/$disk" "$mount_point"
        e2label "/dev/$disk" "$disk_label"

        chown "$username" "$mount_point" 
        # chmod 755 "$mount_point"
    else
        echo "Device /dev/$disk not found."
    fi
done
