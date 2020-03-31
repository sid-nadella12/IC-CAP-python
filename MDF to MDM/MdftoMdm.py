import os, sys, argparse, numpy as np, matplotlib
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
#import json, pandas as pd

def save_json(table_dict):
	# Converts to lists
	new_table_dict = {}
	for table_count, table_list_dict in table_dict.items():
		for var_val, table in table_list_dict.items():
			if table_count not in new_table_dict.keys():
				new_table_dict.update({table_count : []})
			new_table_dict[table_count].append(table.tolist())

	# Saves json
	with open('tables.json', 'w') as jf:
		json.dump(new_table_dict, jf, indent=4, sort_keys=True)

def plot_tables(table_dict):
	# Checks if output folger exists
	out_dir = 'output'
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)

	# Goes through all the tables
	fig = plt.figure()
	for table_count, table_list_dict in table_dict.items():
		# Goes through each table in table_count table_list
		print("Table Count Group: {table_count}")
		print("Number of Tables: {len(table_list_dict.keys())}")
		for i, (var_val, table) in enumerate(table_list_dict.items()):
			# Plots Vout vs Iout NQ
			df = pd.DataFrame(table, columns= ['Vout_NQ(real)', 'Iout_Q(real)', 'Iout_NQ(real)', 'Vin_Q(real)', 'Iin_Q(real)', 'Vin_NQ(real)', 'Iin_NQ(real)'])
			x_l, y_l = 'Vout_NQ(real)', 'Iout_NQ(real)'
			x_i, y_i = 0, 2
			print('var_val:{var_val}')
			plt.plot(table[:, x_i], table[:, y_i], label="Vg = " + str(var_val))
			plt.text(df['Vout_NQ(real)'].max(), df['Iout_NQ(real)'].max(), "Vg = " + str(var_val))
			#fig.suptitle(f'{table_count}: {i+1}')
			plt.xlabel(x_l)
			plt.ylabel(y_l)
			
			# Remove '#' for the next two lines, if you want to get graphs for every Vg value in the file.
			#fig.savefig(os.path.join(out_dir, f'{table_count}_{i+1}'))
			#plt.close(fig)

		# Formatting stdout
		print()
	plt.show()
	# fig.savefig(os.path.join(out_dir, 'all.png'))

def print_tables(table_dict):
	# Goes through table counts
	for table_count, table_list in table_dict.items():
		print("Table Count Number: {table_count}")
		print("Number of Tables for Table Count: {len(table_list)}")
		for table in table_list:
			for line in table:
				for val in line:
					print(val)
				print()
			print()

def parse_mdf(mdf_path):
	with open(mdf_path) as mdf:
		# Goes through mdf line by line
		table_dict = {}
		for line in mdf:
			# Checks if new table
			if line.strip().startswith('VAR Vgs(real)'):
				# Gets var vg value
				var_val = float(line.split('=')[-1].strip())

				# Goes through table
				count = 0
				table_vals_list = []
				for line in mdf:
					# Checks if end of table
					if line.startswith('END'):
						break

					# Ignores trash lines and comments
					if line.startswith('BEGIN') or line.startswith('%'):
						continue

					# Splits line and converts vals to float
					line_split = line.split()
					line_vals = np.asarray([float(l) for l in line_split])
					table_vals_list.append(line_vals)
					count += 1
				
				# Adds table to table dict
				if str(count) not in table_dict.keys():
					table_dict.update({str(count) : {}})
				# table_dict[str(count)].append(np.asarray(table_vals_list))
				table_dict[str(count)].update({var_val : table_vals_list})

		# Converts all to np arrays
		for table_count, table_list_dict in table_dict.items():
			for var_val, table_list in table_list_dict.items():
				table_dict[table_count][var_val] = np.asarray(table_dict[table_count][var_val])

		# Table dict
		return table_dict

def convert_to_mdm(table_dict):
	# Creates mdm from table dict
	mdm_dict = {}
	for table_count, table_list_dict in table_dict.items():
		# mdm list
		mdm_list = []

		# Get vg info to create header
		vg_list = table_list_dict.keys()
		vg_list = [float(f) for f in vg_list]
		vg_list.sort()

		# Calcs vg stuff
		vg_min, vg_max, vg_num = vg_list[0], vg_list[-1], len(vg_list)
		vg_step = round((vg_max - vg_min) / vg_num, 3)
		# print(f'vg: min, max, num, step = {vg_min}, {vg_max}, {vg_num}, {vg_step}')

		# Calcs vd stuff
		table_list = table_list_dict[vg_list[0]]
		table_col = [float(f) for f in table_list[:, 0]]
		vd_min, vd_max, vd_num = 0.05, round(max(table_col) / 10, 1) * 10, len(table_col)
		vd_step = round((vd_max - vd_min) / vd_num, 3)
		vd_list = [round(f*vd_step + vd_min, 3) for f in range(vd_num-1)]
		vd_list.append(vd_max)
		# print(vd_list)

		# Creates header
		header_list = [
			'! VERSION = 6.00',
			'BEGIN_HEADER',
			' ICCAP_INPUTS',
			'  vd\tV D GROUND SMU1 0.03 LIN\t1\t'+str(vd_min)+'\t'+str(vd_max)+'\t'+str(vd_num)+'\t'+str(vd_step),
			'  vg\tV G GROUND SMU2 0.01 LIN\t2\t'+str(vg_min)+'\t'+str(vg_max)+'\t'+str(vg_num)+'\t'+str(vg_step),
			'  vs\tV S GROUND GND 0 CON\t0',
			'  vb\tV B GROUND GND 0 CON\t0',
			' ICCAP_OUTPUTS',
			'  id\tI D GROUND SMU1 B',
			'  ig\tI G GROUND SMU1 B',
			' ICCAP_VALUES',
			'  W \"100u\"',
			'  L \"0.24u\"',
			'  RcontactDC \"1\"',
  			'  Rtotalport1 \"1\"',
			'  Rtotalport2\"1\"',
			'  TEMP \"27\"',
			'  TNOM \"27.00\"',
			'  TIMEDATE \"\"',
			'  OPERATOR \"\"',
			'  TECHNO \"myTechno\"',
			'  LOT \"myLot\"',
			'  WAFER \"myWafer\"',
			'  CHIP \"myChip\"',
			'  MODULE \"myModule\"',
			'  DEV_NAME \"myDevice\"',
			'  REMARKS \"my Notes\"',
			'END_HEADER',

		]
		# print(header_list)
		mdm_list += header_list

		# Create DBs
		for vg in vg_list:
			# Creates db list and goes though vals
			db_list = [float(f) for f in table_dict[table_count][vg][:, 2]]

			# Write DB header
			mdm_list.append('\nBEGIN_DB')
			mdm_list.append(' ICCAP_VAR vg\t'+ str(vg))
			mdm_list.append(' ICCAP_VAR vs\t0')
			mdm_list.append(' ICCAP_VAR vb\t0')
			mdm_list.append('\n #vd\t\tid\t\t\tig')

			# Writes all id vals from Iout NQ real
			for vd, id_val in zip(vd_list, db_list):
				id_val = "{:e}".format(id_val)                             
				mdm_list.append(str(vd) + '\t\t' + str(id_val) + '\t\t0')
			mdm_list.append('END_DB')

		# Adds to mdm lists
		mdm_dict.update({table_count : mdm_list})

	# Returns dict of mdms
	return mdm_dict

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help='input mdf file path', type=str)
	parser.add_argument('-o', '--output', help='output mdm file path', type=str)
	# print(parser.parse_args())
	return parser.parse_args()

def vg_val(table_count, table_dict):
	table = table_count
	for table_count, table_list_dict in table_dict.items():
		if(table == table_count):
			vg_list = table_list_dict.keys()
			vg_values = vg_list
	return vg_values

def write_mdm(mdm_dict, table_dict, out_dir):
	# Writes mdm files

	# Define the output directory to store the mdm files.
	# # out_dir = 'C:/Users/Dell/Desktop/output'
	# if not os.path.exists(out_dir):
	# 	os.makedirs(out_dir)

	# out_dir = filedialog.askdirectory(parent=application_window,
 #                                 initialdir=os.getcwd(),
 #                                 title="Please select a folder:")

	for table_count, mdm_list in mdm_dict.items():
		# Creates file name and writes file
		vg_values = vg_val(table_count, table_dict)
		# sorted_vg_values = vg_values.sort()
		fname = 'VG'
		for vg in vg_values:
			if vg < 0: 
				neg_vg = abs(vg)
				# neg_vg = str(neg_vg)
				fname = fname + 'm' + (str(neg_vg).replace('.', 'p'))   
			if vg > 0:
				vg = abs(vg)
				fname = fname + (str(vg).replace('.', 'p'))		
		with open(os.path.join(out_dir, fname + '.mdm'), 'w') as of:
			of.write('\n'.join(mdm_list))

def main():
	# Gets args
	# args = parse_args()
	# print(args.input)

	# Input file path
	application_window = tk.Tk()

	my_filetypes = [ ('mdf files', '*.mdf'), ('all files', '*.*')]

	file = filedialog.askopenfilename(parent=application_window,
                                    initialdir=os.getcwd(),
                                    title="Please select a file:",
                                    filetypes=my_filetypes)
	# file = 'C:/Users/Dell/Desktop/EE work/parse_mdf/SEI_VGQM5VDQ015_T25_IV.mdf'
	print("select the output directory")
	out_dir = filedialog.askdirectory(parent=application_window,
                                 initialdir=os.getcwd(),
                                 title="Please select a folder:")

	# Parses mdf file to np arrays
	# table_dict = parse_mdf(args.input)
	table_dict = parse_mdf(file)

	# plot_tables(table_dict)
	# save_json(table_dict)

	#Converts to mdm
	mdm_dict = convert_to_mdm(table_dict)

	# Writes mdms
	write_mdm(mdm_dict, table_dict, out_dir)

if __name__ == '__main__':
	main()
