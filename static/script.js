function login() {
    window.location.href = "/dashboard";
}

function calculateAttendance() {

    let total = parseInt(document.getElementById("totalClasses").value);
    let attended = parseInt(document.getElementById("classesAttended").value);

    if (isNaN(total) || isNaN(attended) || total <= 0) {

        document.getElementById("attendanceResult").innerHTML =
            "Please enter valid values";

        return;
    }

    let percentage = (attended / total) * 100;

    document.getElementById("attendanceResult").innerHTML =
        "Attendance Percentage: " + percentage.toFixed(2) + "%";
}