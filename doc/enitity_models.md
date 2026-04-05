// Use DBML to define your database structure
// Docs: https://dbml.dbdiagram.io/docs


Table users {
  id uuid [primary key]
  created_at timestamp
  dni varchar(10) unique [note: 'unique']
  password varchar(255)
}


Table animal_types {
  id uuid [primary key]
  name varchar(50)
}

Table animals {
  id uuid [primary key]
  user_id uuid [not null, primary key]
  type_id uuid [not null]
  created_at timestamp
  name varchar(50)
  tag varchar(50)
  date_of_birth timestamp
  initial_weight float [null]
  initial_weight_date timestamp [null]
  last_weight float [null]
  breed verchar(50)
  status varchar
}
Ref user_animals: animals.user_id > users.id // many-to-one
Ref type_animals: animals.type_id > animal_types.id


Table animal_supplie_types {
  id uuid [primary key]
  name varchar(50)
}

Table animal_supplies {
  id uuid [primary key]
  user_id uuid [not null]
  type_id uuid [not null]
  name varchar(50)
  description varchar(255)
  amount float
  critical_amount integer
  unit_of_measurement varchar(25)
}
Ref user_supplies: users.id < animal_supplies.user_id
Ref type_supplies: animal_supplie_types.id < animal_supplies.type_id


Table animal_sales {
  id uuid [primary key]
  user_id uuid [not null]
  buyer_id uuid [not null]
  animal_id uuid [not null]
  sale_date timestamp
  price float [not null]
  price_per_kg float
  weight float
  description varchar(255)
}
Ref user_sales: users.id < animal_sales.user_id
Ref buyer_sales: buyers.id < animal_sales.buyer_id
Ref animal_sales: animals.id < animal_sales.animal_id


Table supplies_purchases {
  id uuid [primary key]
  user_id uuid [not null]
  supplie_id uudi [not null]
  amount float [not null]
  price float [not null]
  purchase_date timestamp
  unit_price float
  unit_of_measurement varchar(25)
}
Ref user_purchases: users.id < supplies_purchases.user_id
Ref supplie_purchases: animal_supplies.id < supplies_purchases.supplie_id


Table buyers {
  id uuid [primary key]
  user_id uuid [not null]
  name varchar(100)
  description varchar(255)
  contact_number varchar(10)
  contact_address varchar(100)
}

Ref user_buyer: users.id < buyers.user_id