class Car(name: String, wheels: Int, val model: String) : Vehicle(name, wheels) {
    fun openSunroof() {
        println("Opening sunroof")
    }
}